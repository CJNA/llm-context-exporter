"""
Security manager for coordinating privacy and security features.

This module provides a high-level interface for managing all security
and privacy aspects of the LLM Context Exporter.
"""

import os
import tempfile
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

from .encryption import FileEncryption
from .detection import SensitiveDataDetector
from .deletion import SecureFileDeleter
from .network_monitor import NetworkActivityMonitor, LocalOnlyValidator
from .redaction import RedactionPrompter


class SecurityManager:
    """
    Coordinates all security and privacy features.
    
    Provides a unified interface for encryption, sensitive data handling,
    secure deletion, and network monitoring.
    """
    
    def __init__(self, 
                 enable_network_monitoring: bool = True,
                 enable_interactive_redaction: bool = True):
        """
        Initialize the security manager.
        
        Args:
            enable_network_monitoring: Whether to monitor network activity
            enable_interactive_redaction: Whether to prompt for redaction
        """
        self.encryption = FileEncryption()
        self.detector = SensitiveDataDetector()
        self.deleter = SecureFileDeleter()
        self.network_monitor = NetworkActivityMonitor()
        self.validator = LocalOnlyValidator()
        self.redaction_prompter = RedactionPrompter(self.detector)
        
        self.enable_network_monitoring = enable_network_monitoring
        self.enable_interactive_redaction = enable_interactive_redaction
        
        # Track temporary files for cleanup
        self._temp_files: List[str] = []
    
    def process_with_security(self, 
                            content: str, 
                            context: str = "",
                            encrypt_output: bool = True,
                            password: Optional[str] = None) -> Dict[str, Any]:
        """
        Process content with full security measures.
        
        Args:
            content: Content to process
            context: Context description for user prompts
            encrypt_output: Whether to encrypt the processed content
            password: Password for encryption (prompted if None and encryption enabled)
            
        Returns:
            Dict with processed content and security metadata
        """
        result = {
            'original_content': content,
            'processed_content': content,
            'context': context,
            'sensitive_data_detected': False,
            'redaction_applied': False,
            'encrypted': False,
            'network_violations': [],
            'temp_files': []
        }
        
        # Start network monitoring if enabled
        if self.enable_network_monitoring:
            self.network_monitor.start_monitoring()
        
        try:
            # Check for sensitive data
            detections = self.detector.detect_sensitive_data(content)
            result['sensitive_data_detected'] = len(detections) > 0
            
            if detections and self.enable_interactive_redaction:
                # Prompt for redaction
                processed_content, redacted = self.redaction_prompter.prompt_for_redaction(
                    content, context
                )
                result['processed_content'] = processed_content
                result['redaction_applied'] = redacted
            
            # Encrypt if requested
            if encrypt_output and result['processed_content']:
                if password is None:
                    password = self._prompt_for_password()
                
                if password:
                    # Create temporary file for encryption
                    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
                        f.write(result['processed_content'])
                        temp_path = f.name
                    
                    self._temp_files.append(temp_path)
                    
                    # Encrypt the file
                    encrypted_path = self.encryption.encrypt_file(temp_path, password)
                    result['encrypted'] = True
                    result['encrypted_file'] = encrypted_path
                    
                    # Securely delete the temporary file
                    self.deleter.secure_delete(temp_path)
                    self._temp_files.remove(temp_path)
            
        finally:
            # Stop network monitoring and check for violations
            if self.enable_network_monitoring:
                self.network_monitor.stop_monitoring()
                violations = self.network_monitor.get_network_calls()
                result['network_violations'] = violations
                
                if violations:
                    print(f"\n⚠ WARNING: {len(violations)} network calls detected during processing!")
                    print("This may violate local-only processing requirements.")
                    for violation in violations[:3]:  # Show first 3
                        print(f"  - {violation['type']}: {violation.get('args', '')}")
                    if len(violations) > 3:
                        print(f"  ... and {len(violations) - 3} more")
        
        return result
    
    def secure_file_operations(self, file_path: str, password: Optional[str] = None) -> Dict[str, Any]:
        """
        Perform secure operations on a file.
        
        Args:
            file_path: Path to the file
            password: Password for encryption/decryption
            
        Returns:
            Dict with operation results
        """
        result = {
            'file_path': file_path,
            'exists': os.path.exists(file_path),
            'is_encrypted': False,
            'operations': []
        }
        
        if not result['exists']:
            return result
        
        # Check if file is encrypted
        result['is_encrypted'] = self.encryption.is_encrypted_file(file_path)
        
        # If encrypted and password provided, offer to decrypt
        if result['is_encrypted'] and password:
            try:
                decrypted_path = file_path.replace('.enc', '_decrypted')
                self.encryption.decrypt_file(file_path, password, decrypted_path)
                result['operations'].append(f"Decrypted to {decrypted_path}")
            except Exception as e:
                result['operations'].append(f"Decryption failed: {e}")
        
        return result
    
    def cleanup_temp_files(self):
        """Securely clean up any temporary files created during processing."""
        for temp_file in self._temp_files[:]:
            if os.path.exists(temp_file):
                self.deleter.secure_delete(temp_file)
            self._temp_files.remove(temp_file)
    
    def secure_export_cleanup(self, export_directory: str):
        """
        Perform secure cleanup of an export directory.
        
        Args:
            export_directory: Directory containing export files
        """
        if not os.path.exists(export_directory):
            return
        
        print(f"Performing secure cleanup of {export_directory}...")
        
        # Securely delete all files in the directory
        success = self.deleter.secure_delete_directory(export_directory, recursive=True)
        
        if success:
            print("✓ Secure cleanup completed.")
        else:
            print("⚠ Some files may not have been securely deleted.")
        
        # Try to wipe free space
        try:
            parent_dir = os.path.dirname(export_directory)
            self.deleter.wipe_free_space(parent_dir, size_mb=10)  # Wipe 10MB of free space
        except Exception as e:
            print(f"Warning: Free space wiping failed: {e}")
    
    def validate_local_only_operation(self, func):
        """
        Decorator to validate that a function performs only local operations.
        
        Args:
            func: Function to validate
            
        Returns:
            Decorated function
        """
        if self.enable_network_monitoring:
            return self.validator.local_only(func)
        else:
            return func
    
    def get_security_summary(self) -> Dict[str, Any]:
        """
        Get a summary of current security settings and status.
        
        Returns:
            Dict with security status information
        """
        return {
            'network_monitoring_enabled': self.enable_network_monitoring,
            'interactive_redaction_enabled': self.enable_interactive_redaction,
            'encryption_available': True,
            'secure_deletion_available': True,
            'temp_files_count': len(self._temp_files),
            'sensitive_data_patterns': len(self.detector.patterns),
        }
    
    def _prompt_for_password(self) -> Optional[str]:
        """Prompt user for encryption password."""
        import getpass
        
        try:
            password = getpass.getpass("Enter password for encryption (or press Enter to skip): ")
            if password:
                confirm = getpass.getpass("Confirm password: ")
                if password != confirm:
                    print("Passwords don't match. Skipping encryption.")
                    return None
            return password or None
        except KeyboardInterrupt:
            print("\nPassword entry cancelled.")
            return None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup temp files."""
        self.cleanup_temp_files()


# Global security manager instance
security_manager = SecurityManager()