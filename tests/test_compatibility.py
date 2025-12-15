"""
Tests for platform compatibility features.
"""

import pytest
import tempfile
import json
import os
from unittest.mock import patch, MagicMock
from datetime import datetime

from llm_context_exporter.core.compatibility import (
    CompatibilityManager, CompatibilityLevel, FormatDiagnostic, 
    PlatformFeature, UnsupportedDataLog
)
from llm_context_exporter.parsers.chatgpt import ChatGPTParser
from llm_context_exporter.core.models import ParsedExport, Conversation, Message


class TestCompatibilityManager:
    """Test the CompatibilityManager class."""
    
    def test_initialization(self):
        """Test that CompatibilityManager initializes correctly."""
        manager = CompatibilityManager()
        
        assert manager.unsupported_data_log == []
        assert "chatgpt" in manager.platform_features
        assert len(manager.platform_features["chatgpt"]) > 0
        
        # Check that known features are initialized
        feature_names = [f.name for f in manager.platform_features["chatgpt"]]
        assert "Web Browsing" in feature_names
        assert "Plugin Usage" in feature_names
        assert "Code Interpreter" in feature_names
    
    def test_detect_format_with_diagnostics_valid_file(self):
        """Test format detection with a valid ChatGPT export."""
        manager = CompatibilityManager()
        
        # Create a temporary valid JSON file
        valid_export = [
            {
                "id": "test-conv-1",
                "title": "Test Conversation",
                "create_time": 1640995200,  # 2022-01-01
                "messages": [
                    {
                        "role": "user",
                        "content": "Hello",
                        "timestamp": 1640995200
                    }
                ]
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(valid_export, f)
            temp_path = f.name
        
        try:
            diagnostic = manager.detect_format_with_diagnostics(temp_path, ChatGPTParser)
            
            assert isinstance(diagnostic, FormatDiagnostic)
            assert diagnostic.detected_version in ChatGPTParser.SUPPORTED_VERSIONS
            assert diagnostic.compatibility_level in [
                CompatibilityLevel.FULLY_SUPPORTED, 
                CompatibilityLevel.LIMITED_SUPPORT
            ]
            assert diagnostic.confidence > 0.0
            
        finally:
            os.unlink(temp_path)
    
    def test_detect_format_with_diagnostics_invalid_file(self):
        """Test format detection with an invalid file."""
        manager = CompatibilityManager()
        
        # Create a temporary invalid file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content {")
            temp_path = f.name
        
        try:
            diagnostic = manager.detect_format_with_diagnostics(temp_path, ChatGPTParser)
            
            # ChatGPT parser returns "unknown" for invalid files, not "error"
            assert diagnostic.detected_version == "unknown"
            assert diagnostic.compatibility_level == CompatibilityLevel.LIMITED_SUPPORT
            assert diagnostic.confidence == 0.5
            assert len(diagnostic.issues) > 0
            assert len(diagnostic.suggestions) > 0
            
        finally:
            os.unlink(temp_path)
    
    def test_find_fallback_version(self):
        """Test fallback version detection."""
        manager = CompatibilityManager()
        
        supported_versions = ["2023-04-01", "2023-06-01", "2024-01-01", "unknown"]
        
        # Test with unknown version
        fallback = manager._find_fallback_version("unknown", supported_versions)
        assert fallback == "2024-01-01"  # Should return latest known version
        
        # Test with newer version
        fallback = manager._find_fallback_version("2024-06-01", supported_versions)
        assert fallback == "2024-01-01"  # Should return latest older version
        
        # Test with older version
        fallback = manager._find_fallback_version("2022-01-01", supported_versions)
        assert fallback == "2023-04-01"  # Should return oldest supported version
    
    def test_identify_platform_features(self):
        """Test identification of platform-specific features."""
        manager = CompatibilityManager()
        
        # Create a parsed export with platform-specific content
        conversations = [
            Conversation(
                id="conv1",
                title="Web Browsing Test",
                created_at=datetime.now(),
                updated_at=datetime.now(),
                messages=[
                    Message(
                        role="assistant",
                        content="I searched the web and found current information about this topic.",
                        timestamp=datetime.now(),
                        metadata={}
                    )
                ]
            ),
            Conversation(
                id="conv2", 
                title="Code Test",
                created_at=datetime.now(),
                updated_at=datetime.now(),
                messages=[
                    Message(
                        role="assistant",
                        content="I executed code using the Python interpreter to solve this.",
                        timestamp=datetime.now(),
                        metadata={}
                    )
                ]
            )
        ]
        
        parsed_export = ParsedExport(
            format_version="2024-01-01",
            export_date=datetime.now(),
            conversations=conversations,
            metadata={}
        )
        
        features = manager.identify_platform_features(parsed_export)
        
        assert len(features) >= 2
        feature_names = [f.name for f in features]
        assert "Web Browsing" in feature_names
        assert "Code Interpreter" in feature_names
    
    def test_log_unsupported_data(self):
        """Test logging of unsupported data types."""
        manager = CompatibilityManager()
        
        # Log some unsupported data
        manager.log_unsupported_data(
            data_type="custom_field",
            location="conversation_123",
            reason="Unknown field type",
            sample_data="sample value"
        )
        
        # Log the same type again (should increment count)
        manager.log_unsupported_data(
            data_type="custom_field",
            location="conversation_123",
            reason="Unknown field type",
            sample_data="another sample"
        )
        
        # Log different type
        manager.log_unsupported_data(
            data_type="plugin_data",
            location="message_456",
            reason="Plugin not supported"
        )
        
        assert len(manager.unsupported_data_log) == 2
        
        # Check first entry (should have count = 2)
        first_entry = manager.unsupported_data_log[0]
        assert first_entry.data_type == "custom_field"
        assert first_entry.count == 2
        assert first_entry.sample_data == "sample value"
        
        # Check second entry
        second_entry = manager.unsupported_data_log[1]
        assert second_entry.data_type == "plugin_data"
        assert second_entry.count == 1
    
    def test_get_unsupported_data_summary(self):
        """Test getting summary of unsupported data."""
        manager = CompatibilityManager()
        
        # Test empty log
        summary = manager.get_unsupported_data_summary()
        assert summary["total_types"] == 0
        assert summary["entries"] == []
        
        # Add some data
        manager.log_unsupported_data("type1", "loc1", "reason1")
        manager.log_unsupported_data("type1", "loc1", "reason1")  # Increment count
        manager.log_unsupported_data("type2", "loc2", "reason2")
        
        summary = manager.get_unsupported_data_summary()
        assert summary["total_types"] == 2
        assert summary["total_occurrences"] == 3
        assert len(summary["entries"]) == 2
    
    @patch('subprocess.run')
    @patch('shutil.which')
    def test_verify_ollama_installation_not_found(self, mock_which, mock_run):
        """Test Ollama verification when not installed."""
        mock_which.return_value = None
        
        manager = CompatibilityManager()
        is_ready, status_info = manager.verify_ollama_installation()
        
        assert not is_ready
        assert not status_info["ollama_found"]
        assert not status_info["ollama_running"]
        assert not status_info["qwen_available"]
        assert len(status_info["issues"]) > 0
        assert len(status_info["suggestions"]) > 0
    
    @patch('subprocess.run')
    @patch('shutil.which')
    def test_verify_ollama_installation_found_but_not_running(self, mock_which, mock_run):
        """Test Ollama verification when installed but not running."""
        mock_which.return_value = "/usr/local/bin/ollama"
        
        # Mock version check success
        version_result = MagicMock()
        version_result.returncode = 0
        version_result.stdout = "ollama version 0.1.0"
        
        # Mock list command failure (not running)
        list_result = MagicMock()
        list_result.returncode = 1
        
        mock_run.side_effect = [version_result, list_result]
        
        manager = CompatibilityManager()
        is_ready, status_info = manager.verify_ollama_installation()
        
        assert not is_ready
        assert status_info["ollama_found"]
        assert not status_info["ollama_running"]
        assert not status_info["qwen_available"]
        assert status_info["version"] == "ollama version 0.1.0"
        assert "not running" in " ".join(status_info["issues"]).lower()
    
    @patch('subprocess.run')
    @patch('shutil.which')
    def test_verify_ollama_installation_ready(self, mock_which, mock_run):
        """Test Ollama verification when fully ready."""
        mock_which.return_value = "/usr/local/bin/ollama"
        
        # Mock version check success
        version_result = MagicMock()
        version_result.returncode = 0
        version_result.stdout = "ollama version 0.1.0"
        
        # Mock list command success with qwen
        list_result = MagicMock()
        list_result.returncode = 0
        list_result.stdout = "NAME\tID\tSIZE\tMODIFIED\nqwen:latest\tabc123\t4.1GB\t2 days ago"
        
        mock_run.side_effect = [version_result, list_result]
        
        manager = CompatibilityManager()
        is_ready, status_info = manager.verify_ollama_installation()
        
        assert is_ready
        assert status_info["ollama_found"]
        assert status_info["ollama_running"]
        assert status_info["qwen_available"]
        assert status_info["version"] == "ollama version 0.1.0"
        assert len(status_info["issues"]) == 0
    
    def test_generate_compatibility_report(self):
        """Test generation of comprehensive compatibility report."""
        manager = CompatibilityManager()
        
        # Create test data
        conversations = [
            Conversation(
                id="conv1",
                title="Test with web browsing",
                created_at=datetime.now(),
                updated_at=datetime.now(),
                messages=[
                    Message(
                        role="assistant",
                        content="I browsed the web to find this information.",
                        timestamp=datetime.now(),
                        metadata={}
                    )
                ]
            )
        ]
        
        parsed_export = ParsedExport(
            format_version="2024-01-01",
            export_date=datetime.now(),
            conversations=conversations,
            metadata={}
        )
        
        # Add some unsupported data
        manager.log_unsupported_data("test_type", "test_location", "test_reason")
        
        # Generate report for Gemini
        report = manager.generate_compatibility_report(parsed_export, "gemini")
        
        assert "export_info" in report
        assert "platform_features" in report
        assert "unsupported_data" in report
        assert "target_platform_status" in report
        assert "recommendations" in report
        
        # Check export info
        export_info = report["export_info"]
        assert export_info["format_version"] == "2024-01-01"
        assert export_info["conversations_count"] == 1
        
        # Check platform features
        assert len(report["platform_features"]) >= 1
        web_browsing_feature = next(
            (f for f in report["platform_features"] if f["name"] == "Web Browsing"), 
            None
        )
        assert web_browsing_feature is not None
        assert not web_browsing_feature["supported_in_target"]
        
        # Check target platform status
        target_status = report["target_platform_status"]
        assert target_status["platform"] == "gemini"
        assert target_status["ready"] is True  # Gemini doesn't require setup
        
        # Check recommendations
        assert len(report["recommendations"]) > 0


class TestCompatibilityIntegration:
    """Integration tests for compatibility features."""
    
    def test_chatgpt_parser_with_compatibility(self):
        """Test that ChatGPT parser uses compatibility manager correctly."""
        # Create a test export with some unsupported fields
        test_export = {
            "conversations": [
                {
                    "id": "conv1",
                    "title": "Test Conversation",
                    "create_time": 1640995200,
                    "custom_field": "unsupported_value",  # This should be logged
                    "messages": [
                        {
                            "role": "user",
                            "content": "Hello",
                            "timestamp": 1640995200,
                            "unknown_field": "test"  # This should be logged
                        },
                        {
                            "role": "system",  # This should be logged as unsupported role
                            "content": "System message",
                            "timestamp": 1640995200
                        }
                    ]
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_export, f)
            temp_path = f.name
        
        try:
            parser = ChatGPTParser()
            parsed_export = parser.parse_export(temp_path)
            
            # Should successfully parse despite unsupported fields
            assert len(parsed_export.conversations) == 1
            assert len(parsed_export.conversations[0].messages) == 1  # System message filtered out
            assert parsed_export.conversations[0].messages[0].role == "user"
            
        finally:
            os.unlink(temp_path)
    
    def test_unknown_format_fallback(self):
        """Test that unknown format versions fall back gracefully."""
        # Create an export that will be detected as unknown format but still parseable
        test_export = [
            {
                "id": "conv1",
                "title": "Test Conversation",
                "timestamp": 1640995200,  # Using timestamp instead of create_time
                "messages": [
                    {
                        "role": "user",
                        "content": "Hello",
                        "timestamp": 1640995200
                    }
                ]
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_export, f)
            temp_path = f.name
        
        try:
            parser = ChatGPTParser()
            
            # This should parse successfully despite being unknown format
            parsed_export = parser.parse_export(temp_path)
            
            # Should successfully parse
            assert isinstance(parsed_export, ParsedExport)
            assert len(parsed_export.conversations) == 1
            assert parsed_export.conversations[0].title == "Test Conversation"
            assert len(parsed_export.conversations[0].messages) == 1
            
        finally:
            os.unlink(temp_path)