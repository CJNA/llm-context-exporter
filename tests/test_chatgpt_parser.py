"""
Unit tests for ChatGPT export parser.

Tests the ChatGPTParser class functionality including format detection,
parsing of both JSON and ZIP exports, error handling, and metadata preservation.
"""

import json
import os
import tempfile
import zipfile
from datetime import datetime
from unittest import TestCase

from llm_context_exporter.parsers.chatgpt import ChatGPTParser
from llm_context_exporter.parsers.base import ParseError, UnsupportedFormatError


class TestChatGPTParser(TestCase):
    """Test cases for ChatGPT export parser."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parser = ChatGPTParser()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up any temporary files
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_supported_versions(self):
        """Test that parser returns expected supported versions."""
        versions = self.parser.get_supported_versions()
        expected_versions = ["2023-04-01", "2023-06-01", "2024-01-01", "unknown"]
        self.assertEqual(versions, expected_versions)
    
    def test_parse_json_export_mapping_format(self):
        """Test parsing JSON export with mapping format (newer ChatGPT exports)."""
        test_data = [
            {
                "id": "conv-123",
                "title": "Test Conversation",
                "create_time": 1703001600,
                "update_time": 1703002200,
                "mapping": {
                    "node-1": {
                        "message": {
                            "id": "msg-1",
                            "create_time": 1703001600,
                            "author": {"role": "user"},
                            "content": {"parts": ["Hello, how are you?"]}
                        }
                    },
                    "node-2": {
                        "message": {
                            "id": "msg-2",
                            "create_time": 1703001700,
                            "author": {"role": "assistant"},
                            "content": {"parts": ["I'm doing well, thank you!"]}
                        }
                    }
                }
            }
        ]
        
        # Create temporary JSON file
        json_file = os.path.join(self.temp_dir, "test_export.json")
        with open(json_file, 'w') as f:
            json.dump(test_data, f)
        
        # Parse the export
        parsed_export = self.parser.parse_export(json_file)
        
        # Verify results
        self.assertEqual(len(parsed_export.conversations), 1)
        conv = parsed_export.conversations[0]
        self.assertEqual(conv.id, "conv-123")
        self.assertEqual(conv.title, "Test Conversation")
        self.assertEqual(len(conv.messages), 2)
        
        # Check messages
        self.assertEqual(conv.messages[0].role, "user")
        self.assertEqual(conv.messages[0].content, "Hello, how are you?")
        self.assertEqual(conv.messages[1].role, "assistant")
        self.assertEqual(conv.messages[1].content, "I'm doing well, thank you!")
    
    def test_parse_json_export_list_format(self):
        """Test parsing JSON export with list format (older ChatGPT exports)."""
        test_data = [
            {
                "id": "conv-456",
                "title": "Old Format Conversation",
                "timestamp": "2023-12-19T10:00:00Z",
                "messages": [
                    {
                        "role": "user",
                        "content": "What is Python?",
                        "timestamp": "2023-12-19T10:00:00Z"
                    },
                    {
                        "role": "assistant",
                        "content": "Python is a programming language.",
                        "timestamp": "2023-12-19T10:01:00Z"
                    }
                ]
            }
        ]
        
        # Create temporary JSON file
        json_file = os.path.join(self.temp_dir, "test_old_format.json")
        with open(json_file, 'w') as f:
            json.dump(test_data, f)
        
        # Parse the export
        parsed_export = self.parser.parse_export(json_file)
        
        # Verify results
        self.assertEqual(len(parsed_export.conversations), 1)
        conv = parsed_export.conversations[0]
        self.assertEqual(conv.id, "conv-456")
        self.assertEqual(conv.title, "Old Format Conversation")
        self.assertEqual(len(conv.messages), 2)
        
        # Check messages
        self.assertEqual(conv.messages[0].role, "user")
        self.assertEqual(conv.messages[0].content, "What is Python?")
        self.assertEqual(conv.messages[1].role, "assistant")
        self.assertEqual(conv.messages[1].content, "Python is a programming language.")
    
    def test_parse_zip_export(self):
        """Test parsing ZIP export file."""
        conversations_data = [
            {
                "id": "zip-conv-1",
                "title": "ZIP Test Conversation",
                "create_time": 1703020000,
                "update_time": 1703021000,
                "messages": [
                    {
                        "role": "user",
                        "content": "Test message from ZIP",
                        "timestamp": 1703020000
                    }
                ]
            }
        ]
        
        metadata = {
            "export_version": "2023-06-01",
            "export_date": "2023-12-19T12:00:00Z"
        }
        
        # Create temporary ZIP file
        zip_file = os.path.join(self.temp_dir, "test_export.zip")
        with zipfile.ZipFile(zip_file, 'w') as zf:
            zf.writestr('conversations.json', json.dumps(conversations_data))
            zf.writestr('metadata.json', json.dumps(metadata))
        
        # Parse the export
        parsed_export = self.parser.parse_export(zip_file)
        
        # Verify results
        self.assertEqual(len(parsed_export.conversations), 1)
        conv = parsed_export.conversations[0]
        self.assertEqual(conv.id, "zip-conv-1")
        self.assertEqual(conv.title, "ZIP Test Conversation")
        self.assertEqual(len(conv.messages), 1)
        self.assertEqual(conv.messages[0].content, "Test message from ZIP")
        
        # Check metadata was preserved
        self.assertIn('metadata.json', parsed_export.metadata)
    
    def test_format_version_detection_json(self):
        """Test format version detection for JSON files."""
        # Test mapping format (newer)
        mapping_data = [{"mapping": {"node-1": {}}}]
        json_file = os.path.join(self.temp_dir, "mapping_format.json")
        with open(json_file, 'w') as f:
            json.dump(mapping_data, f)
        
        version = self.parser.detect_format_version(json_file)
        self.assertEqual(version, "2024-01-01")
        
        # Test with create_time/update_time (medium)
        time_data = [{"create_time": 123, "update_time": 456}]
        json_file = os.path.join(self.temp_dir, "time_format.json")
        with open(json_file, 'w') as f:
            json.dump(time_data, f)
        
        version = self.parser.detect_format_version(json_file)
        self.assertEqual(version, "2023-06-01")
        
        # Test with basic timestamp (older)
        timestamp_data = [{"timestamp": "2023-01-01"}]
        json_file = os.path.join(self.temp_dir, "timestamp_format.json")
        with open(json_file, 'w') as f:
            json.dump(timestamp_data, f)
        
        version = self.parser.detect_format_version(json_file)
        self.assertEqual(version, "2023-04-01")
    
    def test_format_version_detection_zip(self):
        """Test format version detection for ZIP files."""
        conversations_data = [{"create_time": 123, "update_time": 456}]
        
        zip_file = os.path.join(self.temp_dir, "test_version.zip")
        with zipfile.ZipFile(zip_file, 'w') as zf:
            zf.writestr('conversations.json', json.dumps(conversations_data))
        
        version = self.parser.detect_format_version(zip_file)
        self.assertEqual(version, "2023-06-01")
    
    def test_error_handling_file_not_found(self):
        """Test error handling for non-existent files."""
        with self.assertRaises(FileNotFoundError):
            self.parser.parse_export("nonexistent_file.json")
    
    def test_error_handling_invalid_json(self):
        """Test error handling for invalid JSON."""
        invalid_json_file = os.path.join(self.temp_dir, "invalid.json")
        with open(invalid_json_file, 'w') as f:
            f.write("{ invalid json")
        
        with self.assertRaises(ParseError):
            self.parser.parse_export(invalid_json_file)
    
    def test_error_handling_empty_conversations(self):
        """Test error handling for exports with no valid conversations."""
        empty_data = []
        json_file = os.path.join(self.temp_dir, "empty.json")
        with open(json_file, 'w') as f:
            json.dump(empty_data, f)
        
        with self.assertRaises(ParseError):
            self.parser.parse_export(json_file)
    
    def test_error_handling_corrupted_zip(self):
        """Test error handling for corrupted ZIP files."""
        corrupted_zip = os.path.join(self.temp_dir, "corrupted.zip")
        with open(corrupted_zip, 'w') as f:
            f.write("not a zip file")
        
        with self.assertRaises(ParseError):
            self.parser.parse_export(corrupted_zip)
    
    def test_error_handling_zip_no_conversations(self):
        """Test error handling for ZIP files without conversations."""
        zip_file = os.path.join(self.temp_dir, "no_conversations.zip")
        with zipfile.ZipFile(zip_file, 'w') as zf:
            zf.writestr('metadata.json', '{"version": "1.0"}')
        
        with self.assertRaises(ParseError):
            self.parser.parse_export(zip_file)
    
    def test_timestamp_parsing(self):
        """Test various timestamp format parsing."""
        # Test with Unix timestamp
        test_data = [
            {
                "id": "conv-time",
                "title": "Time Test",
                "create_time": 1703001600,  # Unix timestamp
                "update_time": 1703002200,
                "messages": [
                    {
                        "role": "user",
                        "content": "Test",
                        "timestamp": 1703001600
                    }
                ]
            }
        ]
        
        json_file = os.path.join(self.temp_dir, "time_test.json")
        with open(json_file, 'w') as f:
            json.dump(test_data, f)
        
        parsed_export = self.parser.parse_export(json_file)
        conv = parsed_export.conversations[0]
        
        # Verify timestamps were parsed correctly
        expected_time = datetime.fromtimestamp(1703001600)
        self.assertEqual(conv.created_at, expected_time)
        self.assertEqual(conv.messages[0].timestamp, expected_time)
    
    def test_metadata_preservation(self):
        """Test that message metadata is preserved."""
        test_data = [
            {
                "id": "conv-meta",
                "title": "Metadata Test",
                "create_time": 1703001600,
                "update_time": 1703002200,
                "mapping": {
                    "node-1": {
                        "message": {
                            "id": "msg-1",
                            "create_time": 1703001600,
                            "author": {"role": "user", "name": "TestUser"},
                            "content": {"parts": ["Test message"]},
                            "status": "finished_successfully",
                            "weight": 1.0
                        }
                    }
                }
            }
        ]
        
        json_file = os.path.join(self.temp_dir, "metadata_test.json")
        with open(json_file, 'w') as f:
            json.dump(test_data, f)
        
        parsed_export = self.parser.parse_export(json_file)
        message = parsed_export.conversations[0].messages[0]
        
        # Verify metadata was preserved
        self.assertIn('node_id', message.metadata)
        self.assertIn('message_id', message.metadata)
        self.assertIn('author', message.metadata)
        self.assertIn('status', message.metadata)
        self.assertIn('weight', message.metadata)
        self.assertEqual(message.metadata['status'], 'finished_successfully')
        self.assertEqual(message.metadata['weight'], 1.0)
    
    def test_message_filtering(self):
        """Test that system messages and empty messages are filtered out."""
        test_data = [
            {
                "id": "conv-filter",
                "title": "Filter Test",
                "create_time": 1703001600,
                "update_time": 1703002200,
                "mapping": {
                    "node-1": {
                        "message": {
                            "id": "msg-1",
                            "create_time": 1703001600,
                            "author": {"role": "user"},
                            "content": {"parts": ["Valid user message"]}
                        }
                    },
                    "node-2": {
                        "message": {
                            "id": "msg-2",
                            "create_time": 1703001700,
                            "author": {"role": "system"},
                            "content": {"parts": ["System message - should be filtered"]}
                        }
                    },
                    "node-3": {
                        "message": {
                            "id": "msg-3",
                            "create_time": 1703001800,
                            "author": {"role": "assistant"},
                            "content": {"parts": [""]}  # Empty content
                        }
                    },
                    "node-4": {
                        "message": {
                            "id": "msg-4",
                            "create_time": 1703001900,
                            "author": {"role": "assistant"},
                            "content": {"parts": ["Valid assistant message"]}
                        }
                    }
                }
            }
        ]
        
        json_file = os.path.join(self.temp_dir, "filter_test.json")
        with open(json_file, 'w') as f:
            json.dump(test_data, f)
        
        parsed_export = self.parser.parse_export(json_file)
        messages = parsed_export.conversations[0].messages
        
        # Should only have 2 valid messages (user and assistant, not system or empty)
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0].role, "user")
        self.assertEqual(messages[0].content, "Valid user message")
        self.assertEqual(messages[1].role, "assistant")
        self.assertEqual(messages[1].content, "Valid assistant message")