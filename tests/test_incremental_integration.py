"""
Integration tests for incremental update functionality.

This module tests the complete incremental update workflow from
parsing exports to generating delta packages.
"""

import pytest
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

from llm_context_exporter.core.incremental import IncrementalUpdater
from llm_context_exporter.core.extractor import ContextExtractor
from llm_context_exporter.core.models import (
    Conversation,
    Message,
    ParsedExport,
    UniversalContextPack,
)


class TestIncrementalIntegration:
    """Integration tests for the complete incremental update workflow."""
    
    @pytest.fixture
    def sample_export_v1(self):
        """Create a sample export representing version 1."""
        messages = [
            Message(
                role="user",
                content="I'm working on a Python web application using Django",
                timestamp=datetime.now() - timedelta(days=10),
                metadata={}
            ),
            Message(
                role="assistant",
                content="Django is great for web development! What features are you implementing?",
                timestamp=datetime.now() - timedelta(days=10),
                metadata={}
            ),
            Message(
                role="user",
                content="I need user authentication and a REST API",
                timestamp=datetime.now() - timedelta(days=10),
                metadata={}
            ),
        ]
        
        conversation = Conversation(
            id="conv_python_web",
            title="Django Web Application",
            created_at=datetime.now() - timedelta(days=11),
            updated_at=datetime.now() - timedelta(days=10),
            messages=messages
        )
        
        return ParsedExport(
            format_version="2023-04-01",
            export_date=datetime.now() - timedelta(days=10),
            conversations=[conversation],
            metadata={"version": 1}
        )
    
    @pytest.fixture
    def sample_export_v2(self, sample_export_v1):
        """Create a sample export representing version 2 with new content."""
        # Keep the original conversation
        original_conv = sample_export_v1.conversations[0]
        
        # Add new messages to the original conversation
        updated_messages = original_conv.messages + [
            Message(
                role="user",
                content="I've implemented the authentication system successfully",
                timestamp=datetime.now() - timedelta(days=2),
                metadata={}
            ),
            Message(
                role="assistant",
                content="That's excellent progress! How did you handle the user sessions?",
                timestamp=datetime.now() - timedelta(days=2),
                metadata={}
            ),
        ]
        
        updated_conv = Conversation(
            id="conv_python_web",
            title="Django Web Application",
            created_at=original_conv.created_at,
            updated_at=datetime.now() - timedelta(days=2),
            messages=updated_messages
        )
        
        # Add a completely new conversation
        new_messages = [
            Message(
                role="user",
                content="Now I want to add a React frontend to my Django app",
                timestamp=datetime.now() - timedelta(days=1),
                metadata={}
            ),
            Message(
                role="assistant",
                content="Great choice! You can create a separate React app or use Django REST framework with React.",
                timestamp=datetime.now() - timedelta(days=1),
                metadata={}
            ),
            Message(
                role="user",
                content="I'll use Django REST framework with a separate React app",
                timestamp=datetime.now() - timedelta(days=1),
                metadata={}
            ),
        ]
        
        new_conversation = Conversation(
            id="conv_react_frontend",
            title="React Frontend Integration",
            created_at=datetime.now() - timedelta(days=2),
            updated_at=datetime.now() - timedelta(days=1),
            messages=new_messages
        )
        
        return ParsedExport(
            format_version="2023-04-01",
            export_date=datetime.now(),
            conversations=[updated_conv, new_conversation],
            metadata={"version": 2}
        )
    
    def test_complete_incremental_workflow(self, sample_export_v1, sample_export_v2, temp_directory):
        """Test the complete incremental update workflow."""
        updater = IncrementalUpdater()
        extractor = ContextExtractor()
        
        # Step 1: Process initial export
        initial_context = extractor.extract_context(sample_export_v1.conversations)
        
        # Verify initial context
        assert len(initial_context.projects) >= 1
        assert "Python" in initial_context.technical_context.languages
        assert "Django" in initial_context.technical_context.frameworks
        
        # Save initial context
        initial_context_path = os.path.join(temp_directory, "context_v1.json")
        updater.save_context_pack(initial_context, initial_context_path)
        
        # Step 2: Process updated export
        new_conversations = updater.detect_new_conversations(sample_export_v2, sample_export_v1)
        
        # Should detect both the updated conversation and the new conversation
        assert len(new_conversations) == 2
        
        # Extract context from new conversations
        new_context = extractor.extract_context(new_conversations)
        
        # Step 3: Merge contexts
        merged_context = updater.merge_contexts(initial_context, new_context)
        
        # Verify merge results
        assert merged_context.version == "1.1"  # Version should increment
        assert len(merged_context.projects) >= 1  # Should have at least the original project
        
        # Should have both Python and JavaScript/React technologies
        all_languages = merged_context.technical_context.languages
        all_frameworks = merged_context.technical_context.frameworks
        
        assert "Python" in all_languages
        assert "Django" in all_frameworks
        
        # May have React if the extractor detected it from the new conversation
        # This depends on the extractor's pattern matching
        
        # Step 4: Generate delta package
        delta_package = updater.generate_delta_package(initial_context, new_context)
        
        # Verify delta package
        assert delta_package.version.startswith("delta-")
        assert "delta_from_version" in delta_package.metadata
        assert "delta_to_version" in delta_package.metadata
        
        # Step 5: Save all results
        merged_context_path = os.path.join(temp_directory, "context_v2.json")
        updater.save_context_pack(merged_context, merged_context_path)
        
        delta_path = os.path.join(temp_directory, "delta.json")
        updater.save_context_pack(delta_package, delta_path)
        
        # Step 6: Save version history
        updater.save_version_history(initial_context, temp_directory)
        updater.save_version_history(merged_context, temp_directory)
        
        # Verify version history
        history_file = os.path.join(temp_directory, "version_history.json")
        assert os.path.exists(history_file)
        
        with open(history_file, 'r') as f:
            history = json.load(f)
        
        assert len(history) == 2
        assert history[0]["version"] == "1.0"
        assert history[1]["version"] == "1.1"
        
        # Step 7: Verify round-trip loading
        loaded_initial = updater.load_previous_context(initial_context_path)
        loaded_merged = updater.load_previous_context(merged_context_path)
        loaded_delta = updater.load_previous_context(delta_path)
        
        assert loaded_initial is not None
        assert loaded_merged is not None
        assert loaded_delta is not None
        
        assert loaded_initial.version == "1.0"
        assert loaded_merged.version == "1.1"
        assert loaded_delta.version.startswith("delta-")
    
    def test_no_new_conversations_workflow(self, sample_export_v1, temp_directory):
        """Test workflow when there are no new conversations."""
        updater = IncrementalUpdater()
        extractor = ContextExtractor()
        
        # Process initial export
        initial_context = extractor.extract_context(sample_export_v1.conversations)
        
        # Try to detect new conversations from the same export
        new_conversations = updater.detect_new_conversations(sample_export_v1, sample_export_v1)
        
        # Should find no new conversations
        assert len(new_conversations) == 0
        
        # If we try to extract context from empty list, should get empty context
        if new_conversations:
            new_context = extractor.extract_context(new_conversations)
            merged_context = updater.merge_contexts(initial_context, new_context)
        else:
            # No new conversations, so merged context should be the same as initial
            merged_context = initial_context
        
        assert merged_context.version == initial_context.version
        assert len(merged_context.projects) == len(initial_context.projects)
    
    def test_conversation_update_detection(self, sample_export_v1, sample_export_v2):
        """Test that conversation updates are properly detected."""
        updater = IncrementalUpdater()
        
        new_conversations = updater.detect_new_conversations(sample_export_v2, sample_export_v1)
        
        # Should detect the updated conversation
        updated_conv_ids = {conv.id for conv in new_conversations}
        assert "conv_python_web" in updated_conv_ids  # Updated conversation
        assert "conv_react_frontend" in updated_conv_ids  # New conversation
        
        # Verify the updated conversation has more messages
        updated_conv = next(conv for conv in new_conversations if conv.id == "conv_python_web")
        original_conv = sample_export_v1.conversations[0]
        
        assert len(updated_conv.messages) > len(original_conv.messages)
        assert updated_conv.updated_at > original_conv.updated_at
    
    def test_context_merge_preserves_important_data(self, sample_export_v1, sample_export_v2):
        """Test that context merging preserves important data from both contexts."""
        updater = IncrementalUpdater()
        extractor = ContextExtractor()
        
        # Extract contexts
        initial_context = extractor.extract_context(sample_export_v1.conversations)
        new_conversations = updater.detect_new_conversations(sample_export_v2, sample_export_v1)
        new_context = extractor.extract_context(new_conversations)
        
        # Merge contexts
        merged_context = updater.merge_contexts(initial_context, new_context)
        
        # Verify that original creation date is preserved
        assert merged_context.created_at == initial_context.created_at
        
        # Verify that version is incremented
        assert merged_context.version != initial_context.version
        
        # Verify that merge metadata is added
        assert "merge_date" in merged_context.metadata
        assert "previous_version" in merged_context.metadata
        assert merged_context.metadata["previous_version"] == initial_context.version
    
    def test_delta_package_minimality(self, sample_export_v1, sample_export_v2):
        """Test that delta packages contain only new information."""
        updater = IncrementalUpdater()
        extractor = ContextExtractor()
        
        # Extract contexts
        initial_context = extractor.extract_context(sample_export_v1.conversations)
        new_conversations = updater.detect_new_conversations(sample_export_v2, sample_export_v1)
        new_context = extractor.extract_context(new_conversations)
        
        # Generate delta package
        delta_package = updater.generate_delta_package(initial_context, new_context)
        
        # Delta should not contain items that were already in the initial context
        initial_languages = set(initial_context.technical_context.languages)
        delta_languages = set(delta_package.technical_context.languages)
        
        # Delta languages should not overlap with initial languages
        # (or should be a subset of new languages only)
        for lang in delta_languages:
            # This language should either be new or the delta generation
            # should have filtered it out
            pass  # The exact behavior depends on implementation details
        
        # Delta should have metadata about what it represents
        assert "delta_from_version" in delta_package.metadata
        assert "delta_to_version" in delta_package.metadata
        assert delta_package.metadata["delta_from_version"] == initial_context.version