"""
Integration tests for the complete context extraction workflow.

These tests demonstrate the full context extraction pipeline from
conversations to a complete UniversalContextPack.
"""

import pytest
from datetime import datetime, timedelta
from llm_context_exporter.core.extractor import ContextExtractor
from llm_context_exporter.core.models import (
    Conversation,
    Message,
)


class TestContextExtractionIntegration:
    """Integration tests for the complete context extraction workflow."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = ContextExtractor()
    
    def test_complete_context_extraction_workflow(self):
        """Test the complete context extraction workflow with realistic data."""
        # Create realistic conversation data
        conversations = [
            # Project conversation
            Conversation(
                id="conv1",
                title="E-commerce Platform Development",
                created_at=datetime.now() - timedelta(days=5),
                updated_at=datetime.now() - timedelta(days=5),
                messages=[
                    Message(
                        role="user",
                        content="I'm a senior software engineer working on an e-commerce platform using React, Node.js, and PostgreSQL. I'm having trouble with the payment integration.",
                        timestamp=datetime.now() - timedelta(days=5)
                    ),
                    Message(
                        role="assistant",
                        content="I can help you with payment integration. What payment provider are you using?",
                        timestamp=datetime.now() - timedelta(days=5)
                    ),
                    Message(
                        role="user",
                        content="We're using Stripe. The issue is with handling webhook events for subscription updates.",
                        timestamp=datetime.now() - timedelta(days=5)
                    )
                ]
            ),
            # Technical discussion
            Conversation(
                id="conv2",
                title="Database Optimization",
                created_at=datetime.now() - timedelta(days=3),
                updated_at=datetime.now() - timedelta(days=3),
                messages=[
                    Message(
                        role="user",
                        content="I prefer functional programming in Python and use test-driven development. Need help optimizing database queries.",
                        timestamp=datetime.now() - timedelta(days=3)
                    ),
                    Message(
                        role="assistant",
                        content="TDD is a great approach! For database optimization, let's look at your query patterns.",
                        timestamp=datetime.now() - timedelta(days=3)
                    )
                ]
            ),
            # Mobile project
            Conversation(
                id="conv3",
                title="Mobile App Development",
                created_at=datetime.now() - timedelta(days=1),
                updated_at=datetime.now() - timedelta(days=1),
                messages=[
                    Message(
                        role="user",
                        content="Building a React Native app with Firebase backend. Using VS Code as my editor.",
                        timestamp=datetime.now() - timedelta(days=1)
                    )
                ]
            )
        ]
        
        # Extract context
        context_pack = self.extractor.extract_context(conversations)
        
        # Verify the complete context pack
        assert context_pack.version == "1.0"
        assert context_pack.source_platform == "chatgpt"
        assert context_pack.metadata["total_conversations"] == 3
        
        # Verify user profile
        profile = context_pack.user_profile
        assert profile.role == "senior software engineer"
        assert len(profile.expertise_areas) > 0
        assert "react" in [area.lower() for area in profile.expertise_areas]
        assert len(profile.background_summary) > 0
        
        # Verify projects
        projects = context_pack.projects
        assert len(projects) >= 2  # Should identify at least 2 projects
        
        # Check that projects are sorted by relevance (most recent first)
        if len(projects) >= 2:
            assert projects[0].last_discussed >= projects[1].last_discussed
        
        # Verify at least one project has technical details
        has_tech_stack = any(len(project.tech_stack) > 0 for project in projects)
        assert has_tech_stack
        
        # Verify preferences
        preferences = context_pack.preferences
        assert preferences.coding_style.get("primary_language") == "Python"
        assert preferences.coding_style.get("paradigm") == "functional"
        assert preferences.coding_style.get("testing_approach") == "test-driven"
        assert "vs code" in [tool.lower() for tool in preferences.preferred_tools]
        assert len(preferences.communication_style) > 0
        
        # Verify technical context
        tech_context = context_pack.technical_context
        assert "python" in [lang.lower() for lang in tech_context.languages]
        assert "react" in [fw.lower() for fw in tech_context.frameworks]
        assert "postgresql" in [tool.lower() for tool in tech_context.tools] or "postgres" in [tool.lower() for tool in tech_context.tools]
        assert "web development" in tech_context.domains
        
        # Verify work patterns
        work_patterns = preferences.work_patterns
        assert "usage_frequency" in work_patterns
        assert work_patterns["usage_frequency"] == "occasional"  # 3 conversations
    
    def test_minimal_context_extraction(self):
        """Test context extraction with minimal conversation data."""
        conversations = [
            Conversation(
                id="conv1",
                title="Quick Question",
                created_at=datetime.now(),
                updated_at=datetime.now(),
                messages=[
                    Message(
                        role="user",
                        content="How do I sort an array in JavaScript?",
                        timestamp=datetime.now()
                    ),
                    Message(
                        role="assistant",
                        content="You can use the sort() method.",
                        timestamp=datetime.now()
                    )
                ]
            )
        ]
        
        context_pack = self.extractor.extract_context(conversations)
        
        # Should still create a valid context pack
        assert context_pack.version == "1.0"
        assert context_pack.metadata["total_conversations"] == 1
        
        # May have minimal information but should not crash
        assert isinstance(context_pack.user_profile.background_summary, str)
        assert isinstance(context_pack.projects, list)
        assert isinstance(context_pack.preferences.communication_style, str)
        assert isinstance(context_pack.technical_context.languages, list)
    
    def test_context_extraction_with_multiple_roles(self):
        """Test context extraction when user mentions multiple roles."""
        conversations = [
            Conversation(
                id="conv1",
                title="Career Transition",
                created_at=datetime.now(),
                updated_at=datetime.now(),
                messages=[
                    Message(
                        role="user",
                        content="I'm a data scientist transitioning to become a software engineer. I work with Python and machine learning.",
                        timestamp=datetime.now()
                    )
                ]
            )
        ]
        
        context_pack = self.extractor.extract_context(conversations)
        
        # Should pick up the first role mentioned
        assert context_pack.user_profile.role in ["data scientist", "software engineer"]
        assert "python" in [area.lower() for area in context_pack.user_profile.expertise_areas]
    
    def test_context_extraction_preserves_metadata(self):
        """Test that context extraction preserves important metadata."""
        conversations = [
            Conversation(
                id="conv1",
                title="Test Conversation",
                created_at=datetime.now() - timedelta(days=1),
                updated_at=datetime.now() - timedelta(days=1),
                messages=[
                    Message(
                        role="user",
                        content="Testing the system",
                        timestamp=datetime.now() - timedelta(days=1)
                    )
                ]
            )
        ]
        
        context_pack = self.extractor.extract_context(conversations)
        
        # Check metadata
        metadata = context_pack.metadata
        assert "total_conversations" in metadata
        assert "extraction_date" in metadata
        assert "extractor_version" in metadata
        assert metadata["total_conversations"] == 1
        assert metadata["extractor_version"] == "1.0"
        
        # Check timestamps
        assert context_pack.created_at is not None
        assert isinstance(context_pack.created_at, datetime)