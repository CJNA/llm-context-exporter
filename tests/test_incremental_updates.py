"""
Tests for incremental update functionality.

This module tests the IncrementalUpdater class and its methods for
detecting new conversations, merging contexts, generating delta packages,
and maintaining version history.
"""

import pytest
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

from llm_context_exporter.core.incremental import IncrementalUpdater
from llm_context_exporter.core.models import (
    Conversation,
    Message,
    ParsedExport,
    UniversalContextPack,
    UserProfile,
    ProjectBrief,
    UserPreferences,
    TechnicalContext,
)


class TestIncrementalUpdater:
    """Test cases for the IncrementalUpdater class."""
    
    @pytest.fixture
    def updater(self):
        """Create an IncrementalUpdater instance for testing."""
        return IncrementalUpdater()
    
    @pytest.fixture
    def old_export(self):
        """Create an old export for comparison testing."""
        old_messages = [
            Message(
                role="user",
                content="I'm working on a Python project",
                timestamp=datetime.now() - timedelta(days=5),
                metadata={}
            ),
            Message(
                role="assistant",
                content="That's great! What kind of Python project?",
                timestamp=datetime.now() - timedelta(days=5),
                metadata={}
            ),
        ]
        
        old_conversation = Conversation(
            id="conv_old_1",
            title="Python Project Discussion",
            created_at=datetime.now() - timedelta(days=6),
            updated_at=datetime.now() - timedelta(days=5),
            messages=old_messages
        )
        
        return ParsedExport(
            format_version="2023-04-01",
            export_date=datetime.now() - timedelta(days=5),
            conversations=[old_conversation],
            metadata={"total_conversations": 1}
        )
    
    @pytest.fixture
    def new_export(self, old_export):
        """Create a new export with additional conversations."""
        # Include the old conversation
        old_conversation = old_export.conversations[0]
        
        # Add a new conversation
        new_messages = [
            Message(
                role="user",
                content="Now I'm also working on a React frontend",
                timestamp=datetime.now() - timedelta(days=1),
                metadata={}
            ),
            Message(
                role="assistant",
                content="React is a great choice for frontends!",
                timestamp=datetime.now() - timedelta(days=1),
                metadata={}
            ),
        ]
        
        new_conversation = Conversation(
            id="conv_new_1",
            title="React Frontend Development",
            created_at=datetime.now() - timedelta(days=2),
            updated_at=datetime.now() - timedelta(days=1),
            messages=new_messages
        )
        
        # Also create an updated version of the old conversation
        updated_old_messages = old_conversation.messages + [
            Message(
                role="user",
                content="I've made progress on the Python project",
                timestamp=datetime.now() - timedelta(days=2),
                metadata={}
            )
        ]
        
        updated_old_conversation = Conversation(
            id="conv_old_1",
            title="Python Project Discussion",
            created_at=old_conversation.created_at,
            updated_at=datetime.now() - timedelta(days=2),
            messages=updated_old_messages
        )
        
        return ParsedExport(
            format_version="2023-04-01",
            export_date=datetime.now(),
            conversations=[updated_old_conversation, new_conversation],
            metadata={"total_conversations": 2}
        )
    
    @pytest.fixture
    def existing_context(self):
        """Create an existing context pack for merging tests."""
        return UniversalContextPack(
            version="1.0",
            created_at=datetime.now() - timedelta(days=10),
            source_platform="chatgpt",
            user_profile=UserProfile(
                role="Software Engineer",
                expertise_areas=["Python"],
                background_summary="Python developer"
            ),
            projects=[
                ProjectBrief(
                    name="Python Project",
                    description="A Python application",
                    tech_stack=["Python"],
                    key_challenges=["Performance"],
                    current_status="In Progress",
                    last_discussed=datetime.now() - timedelta(days=5),
                    relevance_score=0.7
                )
            ],
            preferences=UserPreferences(
                coding_style={"primary_language": "Python"},
                communication_style="Direct",
                preferred_tools=["VSCode"],
                work_patterns={"schedule": "flexible"}
            ),
            technical_context=TechnicalContext(
                languages=["Python"],
                frameworks=["Django"],
                tools=["VSCode"],
                domains=["backend development"]
            ),
            metadata={"original": True}
        )
    
    @pytest.fixture
    def new_context(self):
        """Create a new context pack for merging tests."""
        return UniversalContextPack(
            version="1.1",
            created_at=datetime.now(),
            source_platform="chatgpt",
            user_profile=UserProfile(
                role="Full Stack Developer",
                expertise_areas=["Python", "JavaScript", "React"],
                background_summary="Full stack developer with Python and React experience"
            ),
            projects=[
                ProjectBrief(
                    name="Python Project",
                    description="A comprehensive Python web application",
                    tech_stack=["Python", "Django", "PostgreSQL"],
                    key_challenges=["Performance", "Scalability"],
                    current_status="Active Development",
                    last_discussed=datetime.now() - timedelta(days=1),
                    relevance_score=0.9
                ),
                ProjectBrief(
                    name="React Frontend",
                    description="A React-based user interface",
                    tech_stack=["React", "TypeScript"],
                    key_challenges=["State Management"],
                    current_status="Planning",
                    last_discussed=datetime.now() - timedelta(days=1),
                    relevance_score=0.8
                )
            ],
            preferences=UserPreferences(
                coding_style={"primary_language": "Python", "frontend": "React"},
                communication_style="Detailed",
                preferred_tools=["VSCode", "Git"],
                work_patterns={"schedule": "flexible", "testing": "TDD"}
            ),
            technical_context=TechnicalContext(
                languages=["Python", "JavaScript", "TypeScript"],
                frameworks=["Django", "React"],
                tools=["VSCode", "Git"],
                domains=["backend development", "frontend development"]
            ),
            metadata={"updated": True}
        )
    
    def test_detect_new_conversations_completely_new(self, updater, old_export, new_export):
        """Test detecting completely new conversations."""
        new_conversations = updater.detect_new_conversations(new_export, old_export)
        
        # Should find the new conversation
        assert len(new_conversations) == 2  # 1 new + 1 updated
        
        # Check that we found the new conversation
        new_conv_ids = {conv.id for conv in new_conversations}
        assert "conv_new_1" in new_conv_ids
        assert "conv_old_1" in new_conv_ids  # Updated conversation
    
    def test_detect_new_conversations_no_changes(self, updater, old_export):
        """Test detecting new conversations when there are no changes."""
        new_conversations = updater.detect_new_conversations(old_export, old_export)
        
        # Should find no new conversations
        assert len(new_conversations) == 0
    
    def test_merge_contexts_user_profiles(self, updater, existing_context, new_context):
        """Test merging user profiles."""
        merged = updater.merge_contexts(existing_context, new_context)
        
        # Should use newer role
        assert merged.user_profile.role == "Full Stack Developer"
        
        # Should merge expertise areas
        assert "Python" in merged.user_profile.expertise_areas
        assert "JavaScript" in merged.user_profile.expertise_areas
        assert "React" in merged.user_profile.expertise_areas
        
        # Should use longer background summary
        assert "Full stack developer" in merged.user_profile.background_summary
    
    def test_merge_contexts_projects(self, updater, existing_context, new_context):
        """Test merging projects with conflict resolution."""
        merged = updater.merge_contexts(existing_context, new_context)
        
        # Should have 2 projects (1 merged, 1 new)
        assert len(merged.projects) == 2
        
        # Find the merged Python project
        python_project = next(p for p in merged.projects if p.name == "Python Project")
        
        # Should merge tech stacks
        assert "Python" in python_project.tech_stack
        assert "Django" in python_project.tech_stack
        assert "PostgreSQL" in python_project.tech_stack
        
        # Should merge challenges
        assert "Performance" in python_project.key_challenges
        assert "Scalability" in python_project.key_challenges
        
        # Should use more recent last_discussed
        assert python_project.last_discussed == new_context.projects[0].last_discussed
        
        # Should use higher relevance score
        assert python_project.relevance_score == 0.9
    
    def test_merge_contexts_technical_context(self, updater, existing_context, new_context):
        """Test merging technical contexts."""
        merged = updater.merge_contexts(existing_context, new_context)
        
        # Should merge all technical items
        assert "Python" in merged.technical_context.languages
        assert "JavaScript" in merged.technical_context.languages
        assert "TypeScript" in merged.technical_context.languages
        
        assert "Django" in merged.technical_context.frameworks
        assert "React" in merged.technical_context.frameworks
        
        assert "VSCode" in merged.technical_context.tools
        assert "Git" in merged.technical_context.tools
        
        assert "backend development" in merged.technical_context.domains
        assert "frontend development" in merged.technical_context.domains
    
    def test_merge_contexts_version_increment(self, updater, existing_context, new_context):
        """Test that version is properly incremented during merge."""
        merged = updater.merge_contexts(existing_context, new_context)
        
        # Version should be incremented
        assert merged.version == "1.1"
        
        # Should preserve original creation date
        assert merged.created_at == existing_context.created_at
        
        # Should have merge metadata
        assert "merge_date" in merged.metadata
        assert merged.metadata["previous_version"] == "1.0"
        assert merged.metadata["merge_source"] == "incremental_update"
    
    def test_generate_delta_package(self, updater, existing_context, new_context):
        """Test generating delta packages with only new information."""
        delta = updater.generate_delta_package(existing_context, new_context)
        
        # Should have delta version
        assert delta.version.startswith("delta-")
        
        # Should only contain new projects
        assert len(delta.projects) == 1
        assert delta.projects[0].name == "React Frontend"
        
        # Should only contain new technical items
        assert "JavaScript" in delta.technical_context.languages
        assert "TypeScript" in delta.technical_context.languages
        assert "Python" not in delta.technical_context.languages  # Already existed
        
        assert "React" in delta.technical_context.frameworks
        assert "Django" not in delta.technical_context.frameworks  # Already existed
        
        # Should have delta metadata
        assert "delta_from_version" in delta.metadata
        assert "new_projects_count" in delta.metadata
        assert delta.metadata["new_projects_count"] == 1
    
    def test_save_and_load_context_pack(self, updater, existing_context, temp_directory):
        """Test saving and loading context packs."""
        output_path = os.path.join(temp_directory, "context.json")
        
        # Save context pack
        updater.save_context_pack(existing_context, output_path)
        
        # Verify file was created
        assert os.path.exists(output_path)
        
        # Load context pack
        loaded_context = updater.load_previous_context(output_path)
        
        # Verify loaded context matches original
        assert loaded_context is not None
        assert loaded_context.version == existing_context.version
        assert loaded_context.source_platform == existing_context.source_platform
        assert loaded_context.user_profile.role == existing_context.user_profile.role
        assert len(loaded_context.projects) == len(existing_context.projects)
        assert loaded_context.projects[0].name == existing_context.projects[0].name
    
    def test_load_nonexistent_context(self, updater):
        """Test loading a context pack that doesn't exist."""
        result = updater.load_previous_context("/nonexistent/path.json")
        assert result is None
    
    def test_save_version_history(self, updater, existing_context, temp_directory):
        """Test saving version history."""
        # Save version history
        updater.save_version_history(existing_context, temp_directory)
        
        # Check that history file was created
        history_file = os.path.join(temp_directory, "version_history.json")
        assert os.path.exists(history_file)
        
        # Load and verify history
        with open(history_file, 'r') as f:
            history = json.load(f)
        
        assert len(history) == 1
        assert history[0]["version"] == "1.0"
        assert history[0]["source_platform"] == "chatgpt"
        assert history[0]["projects_count"] == 1
    
    def test_save_version_history_multiple_versions(self, updater, existing_context, new_context, temp_directory):
        """Test saving multiple versions to history."""
        # Save first version
        updater.save_version_history(existing_context, temp_directory)
        
        # Save second version
        updater.save_version_history(new_context, temp_directory)
        
        # Load and verify history
        history_file = os.path.join(temp_directory, "version_history.json")
        with open(history_file, 'r') as f:
            history = json.load(f)
        
        assert len(history) == 2
        
        # Should be sorted by version
        assert history[0]["version"] == "1.0"
        assert history[1]["version"] == "1.1"
    
    def test_conversation_content_hash(self, updater):
        """Test conversation content hashing for change detection."""
        messages = [
            Message(
                role="user",
                content="Hello world",
                timestamp=datetime.now(),
                metadata={}
            )
        ]
        
        conv1 = Conversation(
            id="test",
            title="Test",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            messages=messages
        )
        
        conv2 = Conversation(
            id="test",
            title="Test",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            messages=messages
        )
        
        # Same content should produce same hash
        hash1 = updater._conversation_content_hash(conv1)
        hash2 = updater._conversation_content_hash(conv2)
        assert hash1 == hash2
        
        # Different content should produce different hash
        conv2.messages[0].content = "Different content"
        hash3 = updater._conversation_content_hash(conv2)
        assert hash1 != hash3
    
    def test_version_to_tuple(self, updater):
        """Test version string to tuple conversion."""
        assert updater._version_to_tuple("1.0") == (1, 0)
        assert updater._version_to_tuple("2.1") == (2, 1)
        assert updater._version_to_tuple("1.0.1") == (1, 0, 1)
        
        # Delta versions should sort last
        assert updater._version_to_tuple("delta-20231214") == (999, 999, 999)
        
        # Invalid versions should sort last
        assert updater._version_to_tuple("invalid") == (999, 999, 999)
    
    def test_merge_preferences_comprehensive(self, updater):
        """Test comprehensive preference merging."""
        existing_prefs = UserPreferences(
            coding_style={"language": "Python", "style": "functional"},
            communication_style="Direct",
            preferred_tools=["VSCode", "Git"],
            work_patterns={"schedule": "flexible", "testing": "unit"}
        )
        
        new_prefs = UserPreferences(
            coding_style={"language": "Python", "frontend": "React", "style": "object-oriented"},
            communication_style="Detailed",
            preferred_tools=["Git", "Docker"],
            work_patterns={"testing": "TDD", "deployment": "CI/CD"}
        )
        
        merged = updater._merge_preferences(existing_prefs, new_prefs)
        
        # Should merge coding styles (new values override)
        assert merged.coding_style["language"] == "Python"
        assert merged.coding_style["frontend"] == "React"
        assert merged.coding_style["style"] == "object-oriented"  # New overrides
        
        # Should use newer communication style
        assert merged.communication_style == "Detailed"
        
        # Should merge tools (union)
        assert "VSCode" in merged.preferred_tools
        assert "Git" in merged.preferred_tools
        assert "Docker" in merged.preferred_tools
        
        # Should merge work patterns (new values override)
        assert merged.work_patterns["schedule"] == "flexible"
        assert merged.work_patterns["testing"] == "TDD"  # New overrides
        assert merged.work_patterns["deployment"] == "CI/CD"