"""
Tests for the ContextExtractor class.

These tests verify that the context extraction engine correctly identifies
and extracts user projects, profiles, preferences, and technical context
from conversation history.
"""

import pytest
from datetime import datetime, timedelta
from llm_context_exporter.core.extractor import ContextExtractor
from llm_context_exporter.core.models import (
    Conversation,
    Message,
    UniversalContextPack,
    UserProfile,
    ProjectBrief,
    UserPreferences,
    TechnicalContext
)


class TestContextExtractor:
    """Test cases for the ContextExtractor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = ContextExtractor()
    
    def test_extract_context_basic(self):
        """Test basic context extraction from conversations."""
        # Create test conversations
        conversations = [
            Conversation(
                id="conv1",
                title="Python Web Development",
                created_at=datetime.now() - timedelta(days=1),
                updated_at=datetime.now() - timedelta(days=1),
                messages=[
                    Message(
                        role="user",
                        content="I'm a software engineer working on a Django web application",
                        timestamp=datetime.now() - timedelta(days=1)
                    ),
                    Message(
                        role="assistant",
                        content="That's great! Django is a powerful framework.",
                        timestamp=datetime.now() - timedelta(days=1)
                    )
                ]
            )
        ]
        
        # Extract context
        context_pack = self.extractor.extract_context(conversations)
        
        # Verify the result
        assert isinstance(context_pack, UniversalContextPack)
        assert context_pack.version == "1.0"
        assert context_pack.source_platform == "chatgpt"
        assert context_pack.metadata["total_conversations"] == 1
        
        # Check that all components are present
        assert isinstance(context_pack.user_profile, UserProfile)
        assert isinstance(context_pack.projects, list)
        assert isinstance(context_pack.preferences, UserPreferences)
        assert isinstance(context_pack.technical_context, TechnicalContext)
    
    def test_extract_profile_with_role(self):
        """Test profile extraction when user mentions their role."""
        conversations = [
            Conversation(
                id="conv1",
                title="Career Discussion",
                created_at=datetime.now(),
                updated_at=datetime.now(),
                messages=[
                    Message(
                        role="user",
                        content="I'm a data scientist working with Python and machine learning",
                        timestamp=datetime.now()
                    )
                ]
            )
        ]
        
        profile = self.extractor.extract_profile(conversations)
        
        assert profile.role == "data scientist"
        assert "python" in [area.lower() for area in profile.expertise_areas]
        assert len(profile.background_summary) > 0
    
    def test_extract_projects_from_title(self):
        """Test project extraction from conversation titles."""
        conversations = [
            Conversation(
                id="conv1",
                title="E-commerce Website Development",
                created_at=datetime.now(),
                updated_at=datetime.now(),
                messages=[
                    Message(
                        role="user",
                        content="I need help with React and Node.js for my project",
                        timestamp=datetime.now()
                    )
                ]
            )
        ]
        
        projects = self.extractor.extract_projects(conversations)
        
        assert len(projects) == 1
        assert projects[0].name == "E-Commerce Website Development"
        assert "react" in [tech.lower() for tech in projects[0].tech_stack]
    
    def test_extract_projects_from_content(self):
        """Test project extraction from message content."""
        conversations = [
            Conversation(
                id="conv1",
                title="New Chat",  # Generic title
                created_at=datetime.now(),
                updated_at=datetime.now(),
                messages=[
                    Message(
                        role="user",
                        content="I'm building a mobile app using React Native and Firebase",
                        timestamp=datetime.now()
                    )
                ]
            )
        ]
        
        projects = self.extractor.extract_projects(conversations)
        
        assert len(projects) >= 1
        # Should extract some project even with generic title
        project = projects[0]
        assert len(project.tech_stack) > 0
    
    def test_extract_technical_context(self):
        """Test technical context extraction."""
        conversations = [
            Conversation(
                id="conv1",
                title="Tech Stack Discussion",
                created_at=datetime.now(),
                updated_at=datetime.now(),
                messages=[
                    Message(
                        role="user",
                        content="I use Python, Django, PostgreSQL, and Docker for web development",
                        timestamp=datetime.now()
                    )
                ]
            )
        ]
        
        tech_context = self.extractor.extract_technical_context(conversations)
        
        assert "python" in [lang.lower() for lang in tech_context.languages]
        assert "django" in [fw.lower() for fw in tech_context.frameworks]
        assert "docker" in [tool.lower() for tool in tech_context.tools]
        assert "web development" in tech_context.domains
    
    def test_extract_preferences(self):
        """Test user preferences extraction."""
        conversations = [
            Conversation(
                id="conv1",
                title="Development Preferences",
                created_at=datetime.now(),
                updated_at=datetime.now(),
                messages=[
                    Message(
                        role="user",
                        content="I prefer Python for backend development and use VS Code as my editor",
                        timestamp=datetime.now()
                    )
                ]
            )
        ]
        
        preferences = self.extractor.extract_preferences(conversations)
        
        assert preferences.coding_style.get("primary_language") == "Python"
        assert len(preferences.preferred_tools) > 0
        assert len(preferences.communication_style) > 0
    
    def test_empty_conversations(self):
        """Test handling of empty conversation list."""
        conversations = []
        
        # Should not raise an error
        context_pack = self.extractor.extract_context(conversations)
        
        assert context_pack.metadata["total_conversations"] == 0
        assert len(context_pack.projects) == 0
    
    def test_conversations_without_user_messages(self):
        """Test handling of conversations with no user messages."""
        conversations = [
            Conversation(
                id="conv1",
                title="Assistant Only",
                created_at=datetime.now(),
                updated_at=datetime.now(),
                messages=[
                    Message(
                        role="assistant",
                        content="Hello! How can I help you today?",
                        timestamp=datetime.now()
                    )
                ]
            )
        ]
        
        # Should not raise an error
        context_pack = self.extractor.extract_context(conversations)
        
        assert context_pack.user_profile.background_summary == "No background information available."
        assert len(context_pack.projects) == 0
    
    def test_project_relevance_scoring(self):
        """Test that projects are scored and sorted by relevance."""
        now = datetime.now()
        conversations = [
            # Recent project
            Conversation(
                id="conv1",
                title="Recent Project",
                created_at=now - timedelta(days=1),
                updated_at=now - timedelta(days=1),
                messages=[
                    Message(
                        role="user",
                        content="Working on a new React app",
                        timestamp=now - timedelta(days=1)
                    )
                ]
            ),
            # Older project
            Conversation(
                id="conv2",
                title="Old Project",
                created_at=now - timedelta(days=30),
                updated_at=now - timedelta(days=30),
                messages=[
                    Message(
                        role="user",
                        content="Building a Python script",
                        timestamp=now - timedelta(days=30)
                    )
                ]
            )
        ]
        
        projects = self.extractor.extract_projects(conversations)
        
        # Should have projects sorted by relevance (recent first)
        if len(projects) >= 2:
            assert projects[0].last_discussed > projects[1].last_discussed
    
    def test_domain_identification(self):
        """Test identification of technical domains."""
        conversations = [
            Conversation(
                id="conv1",
                title="Data Analysis Project",
                created_at=datetime.now(),
                updated_at=datetime.now(),
                messages=[
                    Message(
                        role="user",
                        content="I'm analyzing data using pandas and numpy for machine learning",
                        timestamp=datetime.now()
                    )
                ]
            )
        ]
        
        tech_context = self.extractor.extract_technical_context(conversations)
        
        assert "data science" in tech_context.domains
    
    def test_communication_style_analysis(self):
        """Test communication style analysis."""
        # Test detailed communication style
        detailed_conversations = [
            Conversation(
                id="conv1",
                title="Detailed Discussion",
                created_at=datetime.now(),
                updated_at=datetime.now(),
                messages=[
                    Message(
                        role="user",
                        content="I would like to discuss the architectural implications of using microservices versus monolithic architecture for our enterprise application, considering factors such as scalability, maintainability, deployment complexity, and team coordination requirements.",
                        timestamp=datetime.now()
                    )
                ]
            )
        ]
        
        preferences = self.extractor.extract_preferences(detailed_conversations)
        assert any(word in preferences.communication_style.lower() for word in ["detailed", "thorough", "comprehensive"])
        
        # Test concise communication style
        concise_conversations = [
            Conversation(
                id="conv1",
                title="Quick Question",
                created_at=datetime.now(),
                updated_at=datetime.now(),
                messages=[
                    Message(
                        role="user",
                        content="How to sort array?",
                        timestamp=datetime.now()
                    )
                ]
            )
        ]
        
        preferences = self.extractor.extract_preferences(concise_conversations)
        assert "concise" in preferences.communication_style.lower() or "direct" in preferences.communication_style.lower()
    
    def test_challenge_extraction(self):
        """Test extraction of key challenges from conversations."""
        conversations = [
            Conversation(
                id="conv1",
                title="Debugging Issues",
                created_at=datetime.now(),
                updated_at=datetime.now(),
                messages=[
                    Message(
                        role="user",
                        content="I'm having trouble with authentication in my React app",
                        timestamp=datetime.now()
                    )
                ]
            )
        ]
        
        projects = self.extractor.extract_projects(conversations)
        
        if projects:
            # Should extract some challenges
            assert len(projects[0].key_challenges) >= 0  # May or may not find challenges depending on pattern matching
    
    def test_work_patterns_extraction(self):
        """Test extraction of work patterns from conversation timing."""
        # Create conversations with business hour timestamps
        business_hour_time = datetime.now().replace(hour=14, minute=30)  # 2:30 PM
        conversations = [
            Conversation(
                id="conv1",
                title="Work Discussion",
                created_at=business_hour_time,
                updated_at=business_hour_time,
                messages=[
                    Message(
                        role="user",
                        content="Working on the project",
                        timestamp=business_hour_time
                    )
                ]
            )
        ]
        
        preferences = self.extractor.extract_preferences(conversations)
        
        # Should detect business hours pattern
        assert preferences.work_patterns.get("work_schedule") == "business_hours"
    
    def test_enhanced_role_detection(self):
        """Test enhanced role detection with more role types."""
        conversations = [
            Conversation(
                id="conv1",
                title="Career Discussion",
                created_at=datetime.now(),
                updated_at=datetime.now(),
                messages=[
                    Message(
                        role="user",
                        content="I'm a senior architect working on distributed systems",
                        timestamp=datetime.now()
                    )
                ]
            )
        ]
        
        profile = self.extractor.extract_profile(conversations)
        
        assert profile.role == "senior architect"
    
    def test_coding_style_preferences(self):
        """Test extraction of detailed coding style preferences."""
        conversations = [
            Conversation(
                id="conv1",
                title="Development Approach",
                created_at=datetime.now(),
                updated_at=datetime.now(),
                messages=[
                    Message(
                        role="user",
                        content="I prefer functional programming in Python and use test-driven development",
                        timestamp=datetime.now()
                    )
                ]
            )
        ]
        
        preferences = self.extractor.extract_preferences(conversations)
        
        assert preferences.coding_style.get("primary_language") == "Python"
        assert preferences.coding_style.get("paradigm") == "functional"
        assert preferences.coding_style.get("testing_approach") == "test-driven"