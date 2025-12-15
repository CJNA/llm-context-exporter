"""
Pytest configuration and shared fixtures.

This module contains pytest fixtures and configuration that are shared
across all test modules.
"""

import pytest
from datetime import datetime, timedelta
from typing import List
import tempfile
import os

from llm_context_exporter.models import (
    Conversation,
    Message,
    ParsedExport,
    UniversalContextPack,
    UserProfile,
    ProjectBrief,
    UserPreferences,
    TechnicalContext,
    FilterConfig,
)


@pytest.fixture
def sample_messages() -> List[Message]:
    """Create sample messages for testing."""
    return [
        Message(
            role="user",
            content="I'm working on a Python web application using Django",
            timestamp=datetime.now() - timedelta(days=1),
            metadata={}
        ),
        Message(
            role="assistant", 
            content="That's great! Django is a powerful framework. What specific features are you implementing?",
            timestamp=datetime.now() - timedelta(days=1),
            metadata={}
        ),
        Message(
            role="user",
            content="I need to implement user authentication and a REST API",
            timestamp=datetime.now() - timedelta(days=1),
            metadata={}
        ),
    ]


@pytest.fixture
def sample_conversation(sample_messages) -> Conversation:
    """Create a sample conversation for testing."""
    return Conversation(
        id="conv_123",
        title="Django Web App Development",
        created_at=datetime.now() - timedelta(days=2),
        updated_at=datetime.now() - timedelta(days=1),
        messages=sample_messages
    )


@pytest.fixture
def sample_conversations(sample_conversation) -> List[Conversation]:
    """Create multiple sample conversations for testing."""
    conv2 = Conversation(
        id="conv_456",
        title="React Frontend Setup",
        created_at=datetime.now() - timedelta(days=3),
        updated_at=datetime.now() - timedelta(days=2),
        messages=[
            Message(
                role="user",
                content="How do I set up a React project with TypeScript?",
                timestamp=datetime.now() - timedelta(days=3),
                metadata={}
            ),
            Message(
                role="assistant",
                content="You can use Create React App with the TypeScript template...",
                timestamp=datetime.now() - timedelta(days=3),
                metadata={}
            ),
        ]
    )
    
    return [sample_conversation, conv2]


@pytest.fixture
def sample_parsed_export(sample_conversations) -> ParsedExport:
    """Create a sample parsed export for testing."""
    return ParsedExport(
        format_version="2023-04-01",
        export_date=datetime.now(),
        conversations=sample_conversations,
        metadata={"total_conversations": len(sample_conversations)}
    )


@pytest.fixture
def sample_user_profile() -> UserProfile:
    """Create a sample user profile for testing."""
    return UserProfile(
        role="Software Engineer",
        expertise_areas=["Python", "JavaScript", "Django", "React"],
        background_summary="Experienced full-stack developer with expertise in Python and JavaScript"
    )


@pytest.fixture
def sample_project_brief() -> ProjectBrief:
    """Create a sample project brief for testing."""
    return ProjectBrief(
        name="Django Web App",
        description="A web application built with Django and React",
        tech_stack=["Python", "Django", "React", "TypeScript"],
        key_challenges=["Authentication", "API Design"],
        current_status="In Development",
        last_discussed=datetime.now() - timedelta(days=1),
        relevance_score=0.8
    )


@pytest.fixture
def sample_context_pack(sample_user_profile, sample_project_brief) -> UniversalContextPack:
    """Create a sample universal context pack for testing."""
    return UniversalContextPack(
        version="1.0",
        created_at=datetime.now(),
        source_platform="chatgpt",
        user_profile=sample_user_profile,
        projects=[sample_project_brief],
        preferences=UserPreferences(
            coding_style={"primary_language": "Python"},
            communication_style="Clear and comprehensive",
            preferred_tools=["VSCode", "Git", "Docker"],
            work_patterns={}
        ),
        technical_context=TechnicalContext(
            languages=["Python", "JavaScript", "TypeScript"],
            frameworks=["Django", "React"],
            tools=["VSCode", "Git", "Docker"],
            domains=["web development"]
        ),
        metadata={"test": True}
    )


@pytest.fixture
def sample_filter_config() -> FilterConfig:
    """Create a sample filter configuration for testing."""
    return FilterConfig(
        excluded_conversation_ids=["conv_456"],
        excluded_topics=["React"],
        date_range=None,
        min_relevance_score=0.5
    )


@pytest.fixture
def temp_directory():
    """Create a temporary directory for testing file operations."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def temp_file():
    """Create a temporary file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
        temp_file.write('{"test": "data"}')
        temp_file.flush()
        yield temp_file.name
    
    # Clean up
    if os.path.exists(temp_file.name):
        os.unlink(temp_file.name)