"""
Unit tests for core data models.

Tests the data structures and their validation logic.
"""

import pytest
from datetime import datetime
from llm_context_exporter.models import (
    Message,
    Conversation,
    ParsedExport,
    UniversalContextPack,
    UserProfile,
    ProjectBrief,
    UserPreferences,
    TechnicalContext,
    FilterConfig,
    TargetPlatform,
    MessageRole,
    ValidationCategory,
)


class TestMessage:
    """Test the Message data model."""
    
    def test_message_creation(self):
        """Test creating a message with required fields."""
        timestamp = datetime.now()
        message = Message(
            role="user",
            content="Hello, world!",
            timestamp=timestamp
        )
        
        assert message.role == "user"
        assert message.content == "Hello, world!"
        assert message.timestamp == timestamp
        assert message.metadata == {}
    
    def test_message_with_metadata(self):
        """Test creating a message with metadata."""
        message = Message(
            role="assistant",
            content="Response",
            timestamp=datetime.now(),
            metadata={"model": "gpt-4", "tokens": 100}
        )
        
        assert message.metadata["model"] == "gpt-4"
        assert message.metadata["tokens"] == 100


class TestConversation:
    """Test the Conversation data model."""
    
    def test_conversation_creation(self, sample_messages):
        """Test creating a conversation with messages."""
        created_at = datetime.now()
        updated_at = datetime.now()
        
        conversation = Conversation(
            id="test_123",
            title="Test Conversation",
            created_at=created_at,
            updated_at=updated_at,
            messages=sample_messages
        )
        
        assert conversation.id == "test_123"
        assert conversation.title == "Test Conversation"
        assert conversation.created_at == created_at
        assert conversation.updated_at == updated_at
        assert len(conversation.messages) == len(sample_messages)


class TestParsedExport:
    """Test the ParsedExport data model."""
    
    def test_parsed_export_creation(self, sample_conversations):
        """Test creating a parsed export."""
        export_date = datetime.now()
        
        parsed_export = ParsedExport(
            format_version="2023-04-01",
            export_date=export_date,
            conversations=sample_conversations
        )
        
        assert parsed_export.format_version == "2023-04-01"
        assert parsed_export.export_date == export_date
        assert len(parsed_export.conversations) == len(sample_conversations)
        assert parsed_export.metadata == {}


class TestUniversalContextPack:
    """Test the UniversalContextPack data model."""
    
    def test_context_pack_creation(self, sample_context_pack):
        """Test creating a universal context pack."""
        assert sample_context_pack.version == "1.0"
        assert sample_context_pack.source_platform == "chatgpt"
        assert sample_context_pack.user_profile.role == "Software Engineer"
        assert len(sample_context_pack.projects) == 1
        assert sample_context_pack.projects[0].name == "Django Web App"
    
    def test_context_pack_technical_context(self, sample_context_pack):
        """Test technical context in context pack."""
        tech_context = sample_context_pack.technical_context
        assert "Python" in tech_context.languages
        assert "Django" in tech_context.frameworks
        assert "web development" in tech_context.domains


class TestUserProfile:
    """Test the UserProfile data model."""
    
    def test_user_profile_defaults(self):
        """Test user profile with default values."""
        profile = UserProfile()
        
        assert profile.role is None
        assert profile.expertise_areas == []
        assert profile.background_summary == ""
    
    def test_user_profile_with_data(self):
        """Test user profile with data."""
        profile = UserProfile(
            role="Data Scientist",
            expertise_areas=["Python", "Machine Learning"],
            background_summary="Experienced in ML and data analysis"
        )
        
        assert profile.role == "Data Scientist"
        assert "Python" in profile.expertise_areas
        assert "Machine Learning" in profile.expertise_areas
        assert "ML" in profile.background_summary


class TestProjectBrief:
    """Test the ProjectBrief data model."""
    
    def test_project_brief_creation(self):
        """Test creating a project brief."""
        last_discussed = datetime.now()
        
        project = ProjectBrief(
            name="Test Project",
            description="A test project",
            tech_stack=["Python", "Flask"],
            key_challenges=["Performance", "Scalability"],
            current_status="Active",
            last_discussed=last_discussed,
            relevance_score=0.9
        )
        
        assert project.name == "Test Project"
        assert project.description == "A test project"
        assert "Python" in project.tech_stack
        assert "Performance" in project.key_challenges
        assert project.relevance_score == 0.9


class TestFilterConfig:
    """Test the FilterConfig data model."""
    
    def test_filter_config_defaults(self):
        """Test filter config with default values."""
        config = FilterConfig()
        
        assert config.excluded_conversation_ids == []
        assert config.excluded_topics == []
        assert config.date_range is None
        assert config.min_relevance_score == 0.0
    
    def test_filter_config_with_exclusions(self):
        """Test filter config with exclusions."""
        config = FilterConfig(
            excluded_conversation_ids=["conv_1", "conv_2"],
            excluded_topics=["React", "Vue"],
            min_relevance_score=0.5
        )
        
        assert "conv_1" in config.excluded_conversation_ids
        assert "React" in config.excluded_topics  # Should preserve original case
        assert "Vue" in config.excluded_topics
        assert config.min_relevance_score == 0.5


class TestEnums:
    """Test the enum definitions."""
    
    def test_target_platform_enum(self):
        """Test TargetPlatform enum values."""
        assert TargetPlatform.GEMINI.value == "gemini"
        assert TargetPlatform.OLLAMA.value == "ollama"
    
    def test_message_role_enum(self):
        """Test MessageRole enum values."""
        assert MessageRole.USER.value == "user"
        assert MessageRole.ASSISTANT.value == "assistant"
    
    def test_validation_category_enum(self):
        """Test ValidationCategory enum values."""
        assert ValidationCategory.PROJECT.value == "project"
        assert ValidationCategory.PREFERENCE.value == "preference"
        assert ValidationCategory.TECHNICAL.value == "technical"