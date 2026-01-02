"""
Tests for security and privacy features.

This module tests the encryption, sensitive data detection, secure deletion,
network monitoring, and redaction functionality.
"""

import os
import tempfile
import pytest
import socket
import warnings
from unittest.mock import patch, MagicMock

from llm_context_exporter.security import (
    FileEncryption,
    SensitiveDataDetector,
    SecureFileDeleter,
    NetworkActivityMonitor,
    LocalOnlyValidator,
    RedactionPrompter,
    SecurityManager
)


class TestFileEncryption:
    """Test file encryption functionality."""
    
    def test_encrypt_decrypt_file(self):
        """Test basic file encryption and decryption."""
        encryption = FileEncryption()
        
        # Create test file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            test_content = "This is sensitive test data"
            f.write(test_content)
            test_file = f.name
        
        try:
            # Test encryption
            encrypted_file = encryption.encrypt_file(test_file, "test_password")
            assert os.path.exists(encrypted_file)
            assert encrypted_file.endswith('.enc')
            
            # Test decryption
            decrypted_file = encryption.decrypt_file(encrypted_file, "test_password")
            assert os.path.exists(decrypted_file)
            
            # Verify content
            with open(decrypted_file, 'r') as f:
                decrypted_content = f.read()
            assert decrypted_content == test_content
            
        finally:
            # Cleanup
            for f in [test_file, encrypted_file, decrypted_file]:
                if os.path.exists(f):
                    os.unlink(f)
    
    def test_encrypt_data_raw(self):
        """Test raw data encryption and decryption."""
        encryption = FileEncryption()
        test_data = b"This is test data"
        password = "test_password"
        
        # Encrypt data
        encrypted_data = encryption.encrypt_data(test_data, password)
        assert len(encrypted_data) > len(test_data)
        assert encrypted_data.startswith(b'LLMCTX01')
        
        # Decrypt data
        decrypted_data = encryption.decrypt_data(encrypted_data, password)
        assert decrypted_data == test_data
    
    def test_wrong_password_fails(self):
        """Test that wrong password fails decryption."""
        encryption = FileEncryption()
        test_data = b"Secret data"
        
        encrypted_data = encryption.encrypt_data(test_data, "correct_password")
        
        with pytest.raises(ValueError, match="Decryption failed"):
            encryption.decrypt_data(encrypted_data, "wrong_password")
    
    def test_empty_password_fails(self):
        """Test that empty password is rejected."""
        encryption = FileEncryption()
        
        with pytest.raises(ValueError, match="Password cannot be empty"):
            encryption.encrypt_data(b"data", "")
    
    def test_is_encrypted_file(self):
        """Test encrypted file detection."""
        encryption = FileEncryption()
        
        # Create test file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("test content")
            test_file = f.name
        
        try:
            # File should not be detected as encrypted initially
            assert not encryption.is_encrypted_file(test_file)
            
            # Encrypt file
            encrypted_file = encryption.encrypt_file(test_file, "password")
            
            # Now it should be detected as encrypted
            assert encryption.is_encrypted_file(encrypted_file)
            
        finally:
            for f in [test_file, encrypted_file]:
                if os.path.exists(f):
                    os.unlink(f)


class TestSensitiveDataDetector:
    """Test sensitive data detection functionality."""
    
    def test_detect_email(self):
        """Test email detection."""
        detector = SensitiveDataDetector()
        text = "Contact me at user@example.com for more info"
        
        detections = detector.detect_sensitive_data(text)
        assert len(detections) == 1
        assert detections[0]['type'] == 'email'
        assert detections[0]['value'] == 'user@example.com'
    
    def test_detect_api_key(self):
        """Test API key detection."""
        detector = SensitiveDataDetector()
        text = "Use API key sk-1234567890abcdef1234567890abcdef for authentication"
        
        detections = detector.detect_sensitive_data(text)
        assert len(detections) >= 1
        api_key_detections = [d for d in detections if d['type'] == 'api_key']
        assert len(api_key_detections) == 1
        assert 'sk-1234567890abcdef1234567890abcdef' in api_key_detections[0]['value']
    
    def test_detect_multiple_types(self):
        """Test detection of multiple sensitive data types."""
        detector = SensitiveDataDetector()
        text = """
        Contact: user@example.com
        Phone: 555-123-4567
        API Key: sk-abcdef1234567890abcdef1234567890
        """
        
        detections = detector.detect_sensitive_data(text)
        assert len(detections) >= 2  # At least email and phone
        
        types_found = {d['type'] for d in detections}
        assert 'email' in types_found
        assert 'phone' in types_found
    
    def test_redact_sensitive_data(self):
        """Test sensitive data redaction."""
        detector = SensitiveDataDetector()
        text = "Email me at user@example.com"
        
        redacted = detector.redact_sensitive_data(text)
        assert 'user@example.com' not in redacted
        assert '[REDACTED]' in redacted
    
    def test_has_sensitive_data(self):
        """Test sensitive data presence check."""
        detector = SensitiveDataDetector()
        
        assert detector.has_sensitive_data("Contact user@example.com")
        assert not detector.has_sensitive_data("This is clean text")


class TestSecureFileDeleter:
    """Test secure file deletion functionality."""
    
    def test_secure_delete_file(self):
        """Test secure file deletion."""
        deleter = SecureFileDeleter(passes=1)  # Use 1 pass for speed
        
        # Create test file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Sensitive data to delete")
            test_file = f.name
        
        assert os.path.exists(test_file)
        
        # Secure delete
        success = deleter.secure_delete(test_file)
        assert success
        assert not os.path.exists(test_file)
    
    def test_secure_delete_nonexistent_file(self):
        """Test secure deletion of non-existent file."""
        deleter = SecureFileDeleter()
        
        success = deleter.secure_delete("/nonexistent/file.txt")
        assert success  # Should return True for non-existent files
    
    def test_secure_delete_with_verification(self):
        """Test secure deletion with verification."""
        deleter = SecureFileDeleter(passes=1)
        
        # Create test file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Data to verify deletion")
            test_file = f.name
        
        success = deleter.secure_delete_with_verification(test_file)
        assert success
        assert not os.path.exists(test_file)


class TestNetworkActivityMonitor:
    """Test network activity monitoring functionality."""
    
    def test_monitor_socket_creation(self):
        """Test monitoring of socket creation."""
        monitor = NetworkActivityMonitor()
        
        monitor.start_monitoring()
        
        # Create a socket (should be detected)
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.close()
        except:
            pass
        
        monitor.stop_monitoring()
        
        calls = monitor.get_network_calls()
        assert len(calls) >= 1
        assert any(call['type'] == 'socket_creation' for call in calls)
    
    def test_monitor_context_manager(self):
        """Test network monitoring context manager."""
        monitor = NetworkActivityMonitor()
        
        with pytest.raises(Exception):  # Should raise NetworkViolationError
            with monitor.monitor_context(strict=True):
                # This should trigger a violation
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.close()
                except:
                    pass
    
    def test_local_validator_decorator(self):
        """Test local-only validator decorator."""
        validator = LocalOnlyValidator()
        
        @validator.warn_on_network
        def test_function():
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.close()
            except:
                pass
            return "completed"
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = test_function()
            
            assert result == "completed"
            assert len(w) >= 1
            assert "network calls" in str(w[0].message).lower()


class TestRedactionPrompter:
    """Test redaction prompting functionality."""
    
    @patch('builtins.input')
    def test_prompt_for_redaction_redact_all(self, mock_input):
        """Test prompting with 'redact all' choice."""
        mock_input.return_value = '1'  # Choose "redact all"
        
        prompter = RedactionPrompter()
        text = "Contact user@example.com for details"
        
        result_text, redacted = prompter.prompt_for_redaction(text)
        
        assert redacted
        assert 'user@example.com' not in result_text
        assert '[REDACTED]' in result_text
    
    @patch('builtins.input')
    def test_prompt_for_redaction_keep_all(self, mock_input):
        """Test prompting with 'keep all' choice."""
        mock_input.side_effect = ['2', 'yes']  # Choose "keep all" and confirm
        
        prompter = RedactionPrompter()
        text = "Contact user@example.com for details"
        
        result_text, redacted = prompter.prompt_for_redaction(text)
        
        assert not redacted
        assert result_text == text
    
    @patch('builtins.input')
    def test_prompt_for_redaction_skip_content(self, mock_input):
        """Test prompting with 'skip content' choice."""
        mock_input.return_value = '4'  # Choose "skip content"
        
        prompter = RedactionPrompter()
        text = "Contact user@example.com for details"
        
        result_text, redacted = prompter.prompt_for_redaction(text)
        
        assert redacted
        assert result_text == ""
    
    def test_prompt_for_redaction_no_sensitive_data(self):
        """Test prompting with no sensitive data."""
        prompter = RedactionPrompter()
        text = "This is clean text with no sensitive information"
        
        result_text, redacted = prompter.prompt_for_redaction(text)
        
        assert not redacted
        assert result_text == text


class TestSecurityManager:
    """Test security manager functionality."""
    
    def test_security_manager_initialization(self):
        """Test security manager initialization."""
        manager = SecurityManager(
            enable_network_monitoring=True,
            enable_interactive_redaction=False
        )
        
        assert manager.enable_network_monitoring
        assert not manager.enable_interactive_redaction
        
        summary = manager.get_security_summary()
        assert summary['network_monitoring_enabled']
        assert not summary['interactive_redaction_enabled']
        assert summary['encryption_available']
        assert summary['secure_deletion_available']
    
    def test_process_with_security_no_sensitive_data(self):
        """Test processing content with no sensitive data."""
        manager = SecurityManager(
            enable_network_monitoring=False,
            enable_interactive_redaction=False
        )
        
        content = "This is clean content"
        result = manager.process_with_security(content, encrypt_output=False)
        
        assert result['processed_content'] == content
        assert not result['sensitive_data_detected']
        assert not result['redaction_applied']
        assert not result['encrypted']
    
    def test_context_manager_cleanup(self):
        """Test security manager context manager cleanup."""
        with SecurityManager() as manager:
            # Add some temp files to the manager
            with tempfile.NamedTemporaryFile(delete=False) as f:
                temp_file = f.name
                manager._temp_files.append(temp_file)
        
        # File should be cleaned up after context exit
        assert not os.path.exists(temp_file)
    
    def test_secure_file_operations(self):
        """Test secure file operations."""
        manager = SecurityManager()
        
        # Create test file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("test content")
            test_file = f.name
        
        try:
            result = manager.secure_file_operations(test_file)
            
            assert result['exists']
            assert not result['is_encrypted']
            assert result['file_path'] == test_file
            
        finally:
            if os.path.exists(test_file):
                os.unlink(test_file)


class TestSecurityIntegration:
    """Test integration between security components."""
    
    def test_end_to_end_security_workflow(self):
        """Test complete security workflow."""
        # Create manager with all features disabled for testing
        manager = SecurityManager(
            enable_network_monitoring=False,
            enable_interactive_redaction=False
        )
        
        # Test content with sensitive data
        content = "API key: sk-1234567890abcdef and email: user@example.com"
        
        # Process without encryption
        result = manager.process_with_security(
            content, 
            context="test context",
            encrypt_output=False
        )
        
        assert result['sensitive_data_detected']
        assert result['processed_content'] == content  # No redaction applied
        assert not result['encrypted']
    
    def test_encryption_integration(self):
        """Test encryption integration with security manager."""
        manager = SecurityManager()
        
        # Create test file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("sensitive content")
            test_file = f.name
        
        try:
            # Encrypt file
            encrypted_file = manager.encryption.encrypt_file(test_file, "password")
            assert os.path.exists(encrypted_file)
            
            # Check if file is detected as encrypted
            assert manager.encryption.is_encrypted_file(encrypted_file)
            
            # Decrypt file
            decrypted_file = manager.encryption.decrypt_file(encrypted_file, "password")
            assert os.path.exists(decrypted_file)
            
        finally:
            # Cleanup
            for f in [test_file, encrypted_file, decrypted_file]:
                if os.path.exists(f):
                    os.unlink(f)