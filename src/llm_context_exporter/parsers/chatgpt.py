"""
ChatGPT export parser implementation.

This module handles parsing of official ChatGPT data export files.
Supports both ZIP archives and direct JSON exports with format version detection.
"""

from typing import List, Dict, Any, Optional
import json
import zipfile
import os
import tempfile
from datetime import datetime
from pathlib import Path

from .base import PlatformParser, UnsupportedFormatError, ParseError
from ..core.models import ParsedExport, Conversation, Message
from ..core.compatibility import CompatibilityManager, CompatibilityLevel


class ChatGPTParser(PlatformParser):
    """
    Parser for ChatGPT export files.
    
    Supports both ZIP archives and direct JSON exports from ChatGPT.
    Handles multiple format versions with backward compatibility.
    Preserves all message metadata including timestamps, roles, and content.
    """
    
    SUPPORTED_VERSIONS = ["2023-04-01", "2023-06-01", "2024-01-01", "unknown"]
    
    def parse_export(self, file_path: str) -> ParsedExport:
        """
        Parse ChatGPT export file into normalized conversation format.
        
        Args:
            file_path: Path to the export file (ZIP or JSON)
            
        Returns:
            ParsedExport containing conversations with metadata
            
        Raises:
            UnsupportedFormatError: If format version is not supported
            ParseError: If file is corrupted or invalid
            FileNotFoundError: If file doesn't exist
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Export file not found: {file_path}")
        
        compatibility_manager = CompatibilityManager()
        
        try:
            # Get detailed format diagnostics
            diagnostic = compatibility_manager.detect_format_with_diagnostics(file_path, self.__class__)
            
            # Log diagnostic information
            if diagnostic.issues:
                for issue in diagnostic.issues:
                    print(f"Warning: {issue}")
            
            # Handle different compatibility levels
            if diagnostic.compatibility_level == CompatibilityLevel.UNSUPPORTED:
                raise UnsupportedFormatError(
                    f"Unsupported format version: {diagnostic.detected_version}. "
                    f"Suggestions: {'; '.join(diagnostic.suggestions)}"
                )
            
            format_version = diagnostic.detected_version
            
            # Try fallback parsing if needed
            if diagnostic.compatibility_level == CompatibilityLevel.BACKWARD_COMPATIBLE:
                print(f"Attempting backward-compatible parsing with version {diagnostic.fallback_version}")
                fallback_result = compatibility_manager.attempt_fallback_parsing(
                    file_path, self.__class__, diagnostic.fallback_version
                )
                if fallback_result:
                    return fallback_result
                else:
                    print("Fallback parsing failed, trying with detected version")
            
            # Parse based on file type
            if self._is_zip_file(file_path):
                return self._parse_zip_export(file_path, format_version)
            else:
                return self._parse_json_export(file_path, format_version)
                
        except json.JSONDecodeError as e:
            raise ParseError(f"Invalid JSON format in export file: {e}")
        except zipfile.BadZipFile as e:
            raise ParseError(f"Corrupted ZIP file: {e}")
        except Exception as e:
            raise ParseError(f"Failed to parse export file: {e}")
    
    def detect_format_version(self, file_path: str) -> str:
        """
        Detect the export format version.
        
        Args:
            file_path: Path to the export file
            
        Returns:
            Format version string
            
        Raises:
            ParseError: If version cannot be determined
        """
        try:
            if self._is_zip_file(file_path):
                return self._detect_version_from_zip(file_path)
            else:
                return self._detect_version_from_json(file_path)
        except Exception as e:
            # If we can't detect version, try to parse with unknown version
            # This provides backward compatibility
            return "unknown"
    
    def get_supported_versions(self) -> List[str]:
        """Get list of supported format versions."""
        return self.SUPPORTED_VERSIONS.copy()
    
    def _is_zip_file(self, file_path: str) -> bool:
        """Check if file is a ZIP archive."""
        try:
            with zipfile.ZipFile(file_path, 'r') as zf:
                return True
        except zipfile.BadZipFile:
            return False
    
    def _detect_version_from_zip(self, file_path: str) -> str:
        """Detect version from ZIP export."""
        try:
            with zipfile.ZipFile(file_path, 'r') as zf:
                # Look for conversations.json or similar files
                file_list = zf.namelist()
                
                # Try to find a conversations file
                conversations_file = None
                for filename in file_list:
                    if 'conversations' in filename.lower() and filename.endswith('.json'):
                        conversations_file = filename
                        break
                
                if not conversations_file:
                    return "unknown"
                
                # Read a small sample to detect format
                with zf.open(conversations_file) as f:
                    sample_data = f.read(1024).decode('utf-8', errors='ignore')
                    return self._infer_version_from_content(sample_data)
                    
        except Exception:
            return "unknown"
    
    def _detect_version_from_json(self, file_path: str) -> str:
        """Detect version from JSON export."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # Read first few lines to detect format
                sample_data = f.read(1024)
                return self._infer_version_from_content(sample_data)
        except Exception:
            return "unknown"
    
    def _infer_version_from_content(self, content: str) -> str:
        """Infer version from content structure."""
        try:
            # Check for specific format indicators in order of specificity
            if '"mapping"' in content:
                # Has mapping structure - newest format
                return "2024-01-01"
            elif '"create_time"' in content and '"update_time"' in content:
                # Has timestamp fields - likely 2023-06-01 or later
                return "2023-06-01"
            elif '"timestamp"' in content:
                # Basic timestamp - likely 2023-04-01
                return "2023-04-01"
            elif content.strip().startswith('['):
                # Array format but no specific indicators - assume newer
                return "2024-01-01"
            else:
                return "unknown"
        except Exception:
            return "unknown"
    
    def _parse_zip_export(self, file_path: str, format_version: str) -> ParsedExport:
        """Parse a ZIP export file."""
        conversations = []
        export_metadata = {}
        
        try:
            with zipfile.ZipFile(file_path, 'r') as zf:
                file_list = zf.namelist()
                
                # Find conversations file
                conversations_file = None
                for filename in file_list:
                    if 'conversations' in filename.lower() and filename.endswith('.json'):
                        conversations_file = filename
                        break
                
                if not conversations_file:
                    raise ParseError("No conversations file found in ZIP archive")
                
                # Extract and parse conversations
                with zf.open(conversations_file) as f:
                    conversations_data = json.load(f)
                    conversations = self._parse_conversations_data(conversations_data, format_version)
                
                # Look for additional metadata files
                for filename in file_list:
                    if filename.lower().endswith('.json') and filename != conversations_file:
                        try:
                            with zf.open(filename) as f:
                                metadata = json.load(f)
                                export_metadata[filename] = metadata
                        except Exception:
                            # Skip files that can't be parsed
                            continue
                            
        except zipfile.BadZipFile as e:
            raise ParseError(f"Invalid ZIP file: {e}")
        except json.JSONDecodeError as e:
            raise ParseError(f"Invalid JSON in ZIP archive: {e}")
        
        return ParsedExport(
            format_version=format_version,
            export_date=datetime.now(),  # Use current time if not available
            conversations=conversations,
            metadata=export_metadata
        )
    
    def _parse_json_export(self, file_path: str, format_version: str) -> ParsedExport:
        """Parse a JSON export file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            conversations = self._parse_conversations_data(data, format_version)
            
            return ParsedExport(
                format_version=format_version,
                export_date=datetime.now(),  # Use current time if not available
                conversations=conversations,
                metadata={"source_file": file_path}
            )
            
        except json.JSONDecodeError as e:
            raise ParseError(f"Invalid JSON format: {e}")
        except Exception as e:
            raise ParseError(f"Failed to parse JSON file: {e}")
    
    def _parse_conversations_data(self, data: Any, format_version: str) -> List[Conversation]:
        """Parse conversations data based on format version."""
        conversations = []
        
        try:
            if isinstance(data, list):
                # Array of conversations
                for conv_data in data:
                    conversation = self._parse_single_conversation(conv_data, format_version)
                    if conversation:
                        conversations.append(conversation)
            elif isinstance(data, dict):
                # Single conversation or wrapped format
                if 'conversations' in data:
                    # Wrapped format
                    for conv_data in data['conversations']:
                        conversation = self._parse_single_conversation(conv_data, format_version)
                        if conversation:
                            conversations.append(conversation)
                else:
                    # Single conversation
                    conversation = self._parse_single_conversation(data, format_version)
                    if conversation:
                        conversations.append(conversation)
            else:
                raise ParseError(f"Unexpected data format: {type(data)}")
                
        except Exception as e:
            raise ParseError(f"Failed to parse conversations: {e}")
        
        if not conversations:
            raise ParseError("No valid conversations found in export")
        
        return conversations
    
    def _parse_single_conversation(self, conv_data: Dict[str, Any], format_version: str) -> Optional[Conversation]:
        """Parse a single conversation based on format version."""
        compatibility_manager = CompatibilityManager()
        
        try:
            # Extract basic conversation info
            conv_id = conv_data.get('id', conv_data.get('conversation_id', str(hash(str(conv_data)))))
            title = conv_data.get('title', conv_data.get('name', 'Untitled Conversation'))
            
            # Log unsupported fields
            for key, value in conv_data.items():
                if key not in ['id', 'conversation_id', 'title', 'name', 'create_time', 'created_at', 
                              'update_time', 'updated_at', 'timestamp', 'mapping', 'messages']:
                    compatibility_manager.log_unsupported_data(
                        data_type=f"conversation_field_{key}",
                        location=f"conversation_{conv_id}",
                        reason=f"Unknown conversation field: {key}",
                        sample_data=str(value)[:50] if value else None
                    )
            
            # Handle timestamps based on format version
            created_at = self._parse_timestamp(conv_data.get('create_time', conv_data.get('created_at', conv_data.get('timestamp'))))
            updated_at = self._parse_timestamp(conv_data.get('update_time', conv_data.get('updated_at', conv_data.get('timestamp'))))
            
            # Parse messages
            messages = []
            messages_data = conv_data.get('mapping', conv_data.get('messages', []))
            
            if isinstance(messages_data, dict):
                # Mapping format (newer versions)
                messages = self._parse_mapping_messages(messages_data, compatibility_manager, conv_id)
            elif isinstance(messages_data, list):
                # List format (older versions)
                messages = self._parse_list_messages(messages_data, compatibility_manager, conv_id)
            else:
                compatibility_manager.log_unsupported_data(
                    data_type="messages_format",
                    location=f"conversation_{conv_id}",
                    reason=f"Unexpected messages format: {type(messages_data)}",
                    sample_data=str(messages_data)[:100] if messages_data else None
                )
            
            if not messages:
                # Skip conversations with no messages
                return None
            
            return Conversation(
                id=str(conv_id),
                title=str(title),
                created_at=created_at,
                updated_at=updated_at,
                messages=messages
            )
            
        except Exception as e:
            # Log the error but continue processing other conversations
            print(f"Warning: Failed to parse conversation: {e}")
            return None
    
    def _parse_mapping_messages(self, mapping: Dict[str, Any], compatibility_manager: CompatibilityManager, conv_id: str) -> List[Message]:
        """Parse messages from mapping format (newer ChatGPT exports)."""
        messages = []
        
        # Build message tree and extract in order
        for node_id, node_data in mapping.items():
            if not isinstance(node_data, dict):
                compatibility_manager.log_unsupported_data(
                    data_type="mapping_node_format",
                    location=f"conversation_{conv_id}_node_{node_id}",
                    reason=f"Expected dict but got {type(node_data)}",
                    sample_data=str(node_data)[:50]
                )
                continue
                
            message_data = node_data.get('message')
            if not message_data:
                # Log unsupported node types
                for key in node_data.keys():
                    if key != 'message':
                        compatibility_manager.log_unsupported_data(
                            data_type=f"node_field_{key}",
                            location=f"conversation_{conv_id}_node_{node_id}",
                            reason=f"Unknown node field: {key}",
                            sample_data=str(node_data[key])[:50] if node_data[key] else None
                        )
                continue
                
            # Extract message content
            content_data = message_data.get('content', {})
            if isinstance(content_data, dict):
                content_parts = content_data.get('parts', [])
                
                # Log unsupported content fields
                for key in content_data.keys():
                    if key not in ['parts', 'content_type']:
                        compatibility_manager.log_unsupported_data(
                            data_type=f"content_field_{key}",
                            location=f"conversation_{conv_id}_message_{message_data.get('id', node_id)}",
                            reason=f"Unknown content field: {key}",
                            sample_data=str(content_data[key])[:50] if content_data[key] else None
                        )
            else:
                # Old format where content is directly a string or list
                content_parts = content_data if isinstance(content_data, list) else [content_data]
            
            if not content_parts:
                continue
                
            content = '\n'.join(str(part) for part in content_parts if part)
            if not content.strip():
                continue
                
            # Extract role and timestamp
            author_data = message_data.get('author', {})
            role = author_data.get('role', 'unknown')
            timestamp = self._parse_timestamp(message_data.get('create_time'))
            
            # Log unsupported message fields
            for key, value in message_data.items():
                if key not in ['id', 'author', 'create_time', 'content', 'status', 'weight', 'metadata']:
                    compatibility_manager.log_unsupported_data(
                        data_type=f"message_field_{key}",
                        location=f"conversation_{conv_id}_message_{message_data.get('id', node_id)}",
                        reason=f"Unknown message field: {key}",
                        sample_data=str(value)[:50] if value else None
                    )
            
            # Skip system messages but log them
            if role not in ['user', 'assistant']:
                compatibility_manager.log_unsupported_data(
                    data_type=f"message_role_{role}",
                    location=f"conversation_{conv_id}_message_{message_data.get('id', node_id)}",
                    reason=f"Unsupported message role: {role}",
                    sample_data=content[:50] if content else None
                )
                continue
            
            messages.append(Message(
                role=role,
                content=content,
                timestamp=timestamp,
                metadata={
                    'node_id': node_id,
                    'message_id': message_data.get('id'),
                    'author': message_data.get('author', {}),
                    'status': message_data.get('status'),
                    'weight': message_data.get('weight', 1.0)
                }
            ))
        
        # Sort messages by timestamp
        messages.sort(key=lambda m: m.timestamp)
        return messages
    
    def _parse_list_messages(self, messages_list: List[Dict[str, Any]], compatibility_manager: CompatibilityManager, conv_id: str) -> List[Message]:
        """Parse messages from list format (older ChatGPT exports)."""
        messages = []
        
        for i, msg_data in enumerate(messages_list):
            if not isinstance(msg_data, dict):
                compatibility_manager.log_unsupported_data(
                    data_type="message_format",
                    location=f"conversation_{conv_id}_message_{i}",
                    reason=f"Expected dict but got {type(msg_data)}",
                    sample_data=str(msg_data)[:50]
                )
                continue
                
            content = msg_data.get('content', msg_data.get('text', ''))
            if not content or not content.strip():
                continue
                
            role = msg_data.get('role', msg_data.get('sender', 'unknown'))
            timestamp = self._parse_timestamp(msg_data.get('timestamp', msg_data.get('created_at')))
            
            # Log unsupported message fields
            for key, value in msg_data.items():
                if key not in ['id', 'content', 'text', 'role', 'sender', 'timestamp', 'created_at', 'metadata']:
                    compatibility_manager.log_unsupported_data(
                        data_type=f"message_field_{key}",
                        location=f"conversation_{conv_id}_message_{msg_data.get('id', i)}",
                        reason=f"Unknown message field: {key}",
                        sample_data=str(value)[:50] if value else None
                    )
            
            # Skip system messages but log them
            if role not in ['user', 'assistant']:
                compatibility_manager.log_unsupported_data(
                    data_type=f"message_role_{role}",
                    location=f"conversation_{conv_id}_message_{msg_data.get('id', i)}",
                    reason=f"Unsupported message role: {role}",
                    sample_data=content[:50] if content else None
                )
                continue
            
            messages.append(Message(
                role=role,
                content=str(content),
                timestamp=timestamp,
                metadata={
                    'message_id': msg_data.get('id'),
                    'sender': msg_data.get('sender'),
                    'original_data': msg_data
                }
            ))
        
        return messages
    
    def _parse_timestamp(self, timestamp_value: Any) -> datetime:
        """Parse timestamp from various formats."""
        if not timestamp_value:
            return datetime.now()
            
        try:
            if isinstance(timestamp_value, (int, float)):
                # Unix timestamp
                return datetime.fromtimestamp(timestamp_value)
            elif isinstance(timestamp_value, str):
                # ISO format or other string formats
                try:
                    # Try ISO format first
                    return datetime.fromisoformat(timestamp_value.replace('Z', '+00:00'))
                except ValueError:
                    # Try other common formats
                    for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d']:
                        try:
                            return datetime.strptime(timestamp_value, fmt)
                        except ValueError:
                            continue
                    # If all else fails, use current time
                    return datetime.now()
            else:
                return datetime.now()
        except Exception:
            return datetime.now()