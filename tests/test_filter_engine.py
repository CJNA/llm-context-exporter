"""
Tests for the FilterEngine class.

This module tests the filtering and selection functionality for controlling
what context is included in the exported context packages.
"""

import pytest
import tempfile
import os
import json
from datetime import datetime, timedelta
from typing import List

from llm_context_exporter.core.filter import FilterEngine, FilterableItem
from llm_context_exporter.core.models import (
    UniversalContextPack, FilterConfig, ProjectBrief, UserProfile,
    UserPreferences, TechnicalContext, Conversation, Message
)


class TestFilterEngine:
    """Test the FilterEngine class."""
    
    @pytest.fixture
    def sample_context_pack(self) -> UniversalContextPack:
        """Create a sample context pack for testing."""
        now = datetime.now()
        
        projects = [
            ProjectBrief(
                name="Web App",
                description="A React web application",
                tech_stack=["React", "TypeScript", "Node.js"],
                key_challenges=["Performance optimization", "State management"],
                current_status="In development",
                last_discussed=now - timedelta(days=5),
                relevance_score=0.8
            ),
            ProjectBrief(
                name="Python API",
                description="REST API built with FastAPI",
                tech_stack=["Python", "FastAPI", "PostgreSQL"],
                key_challenges=["Database optimization", "Authentication"],
                current_status="Production",
                last_discussed=now - timedelta(days=30),
                relevance_score=0.6
            ),
            ProjectBrief(
                name="Mobile App",
                description="React Native mobile application",
                tech_stack=["React Native", "JavaScript", "Firebase"],
                key_challenges=["Cross-platform compatibility"],
                current_status="Planning",
                last_discussed=now - timedelta(days=2),
                relevance_score=0.9
            )
        ]
        
        technical_context = TechnicalContext(
            languages=["Python", "JavaScript", "TypeScript"],
            frameworks=["React", "FastAPI", "React Native"],
            tools=["Git", "Docker", "VS Code"],
            domains=["web development", "mobile development", "API development"]
        )
        
        return UniversalContextPack(
            version="1.0",
            created_at=now,
            source_platform="chatgpt",
            user_profile=UserProfile(),
            projects=projects,
            preferences=UserPreferences(),
            technical_context=technical_context
        )
    
    @pytest.fixture
    def sample_conversations(self) -> List[Conversation]:
        """Create sample conversations for testing."""
        now = datetime.now()
        
        conversations = [
            Conversation(
                id="conv_1",
                title="React Development Help",
                created_at=now - timedelta(days=10),
                updated_at=now - timedelta(days=10),
                messages=[
                    Message(role="user", content="How do I optimize React performance?", timestamp=now - timedelta(days=10)),
                    Message(role="assistant", content="Here are some React optimization techniques...", timestamp=now - timedelta(days=10))
                ]
            ),
            Conversation(
                id="conv_2", 
                title="Python API Design",
                created_at=now - timedelta(days=20),
                updated_at=now - timedelta(days=20),
                messages=[
                    Message(role="user", content="Best practices for FastAPI?", timestamp=now - timedelta(days=20)),
                    Message(role="assistant", content="FastAPI best practices include...", timestamp=now - timedelta(days=20))
                ]
            ),
            Conversation(
                id="conv_3",
                title="Mobile Development Questions",
                created_at=now - timedelta(days=5),
                updated_at=now - timedelta(days=5),
                messages=[
                    Message(role="user", content="React Native vs Flutter?", timestamp=now - timedelta(days=5)),
                    Message(role="assistant", content="Here's a comparison...", timestamp=now - timedelta(days=5))
                ]
            )
        ]
        
        return conversations
    
    @pytest.fixture
    def filter_engine(self) -> FilterEngine:
        """Create a FilterEngine instance with temporary preferences file."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as f:
            temp_file = f.name
        
        engine = FilterEngine(preferences_file=temp_file)
        
        yield engine
        
        # Cleanup
        if os.path.exists(temp_file):
            os.unlink(temp_file)
    
    def test_apply_filters_no_exclusions(self, filter_engine: FilterEngine, sample_context_pack: UniversalContextPack):
        """Test applying filters with no exclusions."""
        filters = FilterConfig()
        
        filtered_context = filter_engine.apply_filters(sample_context_pack, filters)
        
        # Should have all projects
        assert len(filtered_context.projects) == 3
        assert filtered_context.metadata["filtered"] is True
        assert filtered_context.metadata["original_project_count"] == 3
        assert filtered_context.metadata["filtered_project_count"] == 3
    
    def test_apply_filters_exclude_topics(self, filter_engine: FilterEngine, sample_context_pack: UniversalContextPack):
        """Test applying filters with topic exclusions."""
        filters = FilterConfig(excluded_topics=["React", "Python"])
        
        filtered_context = filter_engine.apply_filters(sample_context_pack, filters)
        
        # Should exclude projects that use React or Python
        assert len(filtered_context.projects) == 0  # All projects use either React or Python
        assert filtered_context.metadata["filtered"] is True
        assert filtered_context.metadata["original_project_count"] == 3
        assert filtered_context.metadata["filtered_project_count"] == 0
    
    def test_apply_filters_exclude_specific_project(self, filter_engine: FilterEngine, sample_context_pack: UniversalContextPack):
        """Test applying filters to exclude a specific project."""
        filters = FilterConfig(excluded_topics=["Web App"])
        
        filtered_context = filter_engine.apply_filters(sample_context_pack, filters)
        
        # Should exclude the "Web App" project
        assert len(filtered_context.projects) == 2
        project_names = [p.name for p in filtered_context.projects]
        assert "Web App" not in project_names
        assert "Python API" in project_names
        assert "Mobile App" in project_names
    
    def test_apply_filters_relevance_score(self, filter_engine: FilterEngine, sample_context_pack: UniversalContextPack):
        """Test applying filters with minimum relevance score."""
        filters = FilterConfig(min_relevance_score=0.7)
        
        filtered_context = filter_engine.apply_filters(sample_context_pack, filters)
        
        # Should only include projects with relevance >= 0.7
        assert len(filtered_context.projects) == 2
        for project in filtered_context.projects:
            assert project.relevance_score >= 0.7
    
    def test_apply_filters_date_range(self, filter_engine: FilterEngine, sample_context_pack: UniversalContextPack):
        """Test applying filters with date range."""
        now = datetime.now()
        start_date = now - timedelta(days=10)
        end_date = now
        
        filters = FilterConfig(date_range=(start_date, end_date))
        
        filtered_context = filter_engine.apply_filters(sample_context_pack, filters)
        
        # Should only include projects discussed within the date range
        assert len(filtered_context.projects) == 2  # Web App and Mobile App
        for project in filtered_context.projects:
            assert start_date <= project.last_discussed <= end_date
    
    def test_apply_filters_technical_context(self, filter_engine: FilterEngine, sample_context_pack: UniversalContextPack):
        """Test that technical context is filtered based on excluded topics."""
        filters = FilterConfig(excluded_topics=["Python", "React"])
        
        filtered_context = filter_engine.apply_filters(sample_context_pack, filters)
        
        # Technical context should be filtered
        assert "Python" not in filtered_context.technical_context.languages
        assert "React" not in filtered_context.technical_context.frameworks
        assert "TypeScript" in filtered_context.technical_context.languages  # Should remain
        assert "FastAPI" in filtered_context.technical_context.frameworks  # Should remain
    
    def test_get_filterable_items(self, filter_engine: FilterEngine, sample_context_pack: UniversalContextPack):
        """Test getting filterable items from context pack."""
        items = filter_engine.get_filterable_items(sample_context_pack)
        
        # Should have items for projects and technical context
        assert len(items) > 0
        
        # Check for project items
        project_items = [item for item in items if item.item_type == "project"]
        assert len(project_items) == 3
        
        # Check for topic items
        topic_items = [item for item in items if item.item_type == "topic"]
        assert len(topic_items) > 0
        
        # Verify item structure
        for item in items:
            assert hasattr(item, 'item_id')
            assert hasattr(item, 'item_type')
            assert hasattr(item, 'title')
            assert hasattr(item, 'description')
            assert hasattr(item, 'metadata')
    
    def test_get_filterable_conversations(self, filter_engine: FilterEngine, sample_conversations: List[Conversation]):
        """Test getting filterable conversations."""
        items = filter_engine.get_filterable_conversations(sample_conversations)
        
        assert len(items) == 3
        
        for item in items:
            assert item.item_type == "conversation"
            assert item.item_id.startswith("conversation_")
            assert "message_count" in item.metadata
            assert "created_at" in item.metadata
    
    def test_apply_conversation_exclusions(self, filter_engine: FilterEngine, sample_conversations: List[Conversation]):
        """Test applying conversation exclusions."""
        filters = FilterConfig(excluded_conversation_ids=["conv_1", "conv_3"])
        
        filtered_conversations = filter_engine.apply_conversation_exclusions(sample_conversations, filters)
        
        assert len(filtered_conversations) == 1
        assert filtered_conversations[0].id == "conv_2"
    
    def test_create_filter_from_exclusions(self, filter_engine: FilterEngine):
        """Test creating filter config from exclusion list."""
        excluded_items = [
            "project_Web App",
            "language_Python",
            "conversation_conv_1",
            "domain_web development"
        ]
        
        filters = filter_engine.create_filter_from_exclusions(excluded_items)
        
        assert "conv_1" in filters.excluded_conversation_ids
        assert "Web App" in filters.excluded_topics
        assert "Python" in filters.excluded_topics
        assert "web development" in filters.excluded_topics
    
    def test_create_date_range_filter(self, filter_engine: FilterEngine):
        """Test creating date range filter."""
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 12, 31)
        
        filters = filter_engine.create_date_range_filter(start_date, end_date)
        
        assert filters.date_range == (start_date, end_date)
    
    def test_create_date_range_filter_invalid(self, filter_engine: FilterEngine):
        """Test creating date range filter with invalid dates."""
        start_date = datetime(2023, 12, 31)
        end_date = datetime(2023, 1, 1)
        
        with pytest.raises(ValueError, match="Start date must be before end date"):
            filter_engine.create_date_range_filter(start_date, end_date)
    
    def test_create_relevance_filter(self, filter_engine: FilterEngine):
        """Test creating relevance filter."""
        filters = filter_engine.create_relevance_filter(0.5)
        
        assert filters.min_relevance_score == 0.5
    
    def test_create_relevance_filter_invalid(self, filter_engine: FilterEngine):
        """Test creating relevance filter with invalid score."""
        with pytest.raises(ValueError, match="Relevance score must be between 0.0 and 1.0"):
            filter_engine.create_relevance_filter(1.5)
        
        with pytest.raises(ValueError, match="Relevance score must be between 0.0 and 1.0"):
            filter_engine.create_relevance_filter(-0.1)
    
    def test_save_and_load_filter_preferences(self, filter_engine: FilterEngine):
        """Test saving and loading filter preferences."""
        original_filters = FilterConfig(
            excluded_conversation_ids=["conv_1"],
            excluded_topics=["Python", "React"],
            min_relevance_score=0.5
        )
        
        # Save preferences
        filter_engine.save_filter_preferences(original_filters)
        
        # Load preferences
        loaded_filters = filter_engine.load_filter_preferences()
        
        assert loaded_filters.excluded_conversation_ids == original_filters.excluded_conversation_ids
        assert loaded_filters.excluded_topics == original_filters.excluded_topics
        assert loaded_filters.min_relevance_score == original_filters.min_relevance_score
    
    def test_save_and_load_filter_preferences_with_date_range(self, filter_engine: FilterEngine):
        """Test saving and loading filter preferences with date range."""
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 12, 31)
        
        original_filters = FilterConfig(
            excluded_topics=["Python"],
            date_range=(start_date, end_date)
        )
        
        # Save preferences
        filter_engine.save_filter_preferences(original_filters)
        
        # Load preferences
        loaded_filters = filter_engine.load_filter_preferences()
        
        assert loaded_filters.date_range == (start_date, end_date)
        assert loaded_filters.excluded_topics == original_filters.excluded_topics
    
    def test_load_filter_preferences_no_file(self, filter_engine: FilterEngine):
        """Test loading filter preferences when no file exists."""
        # Ensure file doesn't exist
        if os.path.exists(filter_engine.preferences_file):
            os.unlink(filter_engine.preferences_file)
        
        loaded_filters = filter_engine.load_filter_preferences()
        
        # Should return empty config
        assert loaded_filters.excluded_conversation_ids == []
        assert loaded_filters.excluded_topics == []
        assert loaded_filters.date_range is None
        assert loaded_filters.min_relevance_score == 0.0
    
    def test_get_filter_summary(self, filter_engine: FilterEngine, sample_context_pack: UniversalContextPack):
        """Test getting filter summary."""
        filters = FilterConfig(excluded_topics=["React"])
        filtered_context = filter_engine.apply_filters(sample_context_pack, filters)
        
        summary = filter_engine.get_filter_summary(sample_context_pack, filtered_context)
        
        assert "projects_removed" in summary
        assert "projects_remaining" in summary
        assert "removed_project_names" in summary
        assert "filter_applied_at" in summary
        assert "coherence_maintained" in summary
        
        assert summary["projects_removed"] > 0
        assert summary["projects_remaining"] >= 0
        assert len(summary["removed_project_names"]) == summary["projects_removed"]
    
    def test_is_topic_excluded_exact_match(self, filter_engine: FilterEngine):
        """Test topic exclusion with exact match."""
        excluded_topics = ["Python", "React"]
        
        assert filter_engine._is_topic_excluded("Python", excluded_topics)
        assert filter_engine._is_topic_excluded("python", excluded_topics)  # Case insensitive
        assert not filter_engine._is_topic_excluded("JavaScript", excluded_topics)
    
    def test_is_topic_excluded_partial_match(self, filter_engine: FilterEngine):
        """Test topic exclusion with partial match."""
        excluded_topics = ["React"]
        
        assert filter_engine._is_topic_excluded("React Native", excluded_topics)
        assert filter_engine._is_topic_excluded("react-router", excluded_topics)
        assert not filter_engine._is_topic_excluded("Vue", excluded_topics)
    
    def test_filter_preserves_coherence(self, filter_engine: FilterEngine, sample_context_pack: UniversalContextPack):
        """Test that filtering preserves context coherence."""
        # Filter out one technology but keep projects that use other technologies
        filters = FilterConfig(excluded_topics=["PostgreSQL"])
        
        filtered_context = filter_engine.apply_filters(sample_context_pack, filters)
        
        # Should still have projects (coherence maintained)
        assert len(filtered_context.projects) > 0
        
        # User profile and preferences should be preserved
        assert filtered_context.user_profile == sample_context_pack.user_profile
        assert filtered_context.preferences == sample_context_pack.preferences
        
        # Technical context should be filtered but not empty
        assert len(filtered_context.technical_context.languages) > 0
        assert len(filtered_context.technical_context.frameworks) > 0