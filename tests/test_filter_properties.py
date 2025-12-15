"""
Property-based tests for the FilterEngine class.

This module contains property-based tests that verify universal properties
of the filtering system across randomly generated inputs.
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from datetime import datetime, timedelta
from typing import List
import tempfile
import os

from llm_context_exporter.core.filter import FilterEngine, FilterableItem
from llm_context_exporter.core.models import (
    UniversalContextPack, FilterConfig, ProjectBrief, UserProfile,
    UserPreferences, TechnicalContext, Conversation, Message
)


# Hypothesis strategies for generating test data

@st.composite
def conversation_strategy(draw):
    """Generate a random conversation."""
    conv_id = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    title = draw(st.text(min_size=1, max_size=100))
    
    # Generate timestamps using fixed base time
    base_time = datetime(2023, 1, 1) + timedelta(days=draw(st.integers(min_value=1, max_value=365)))
    created_at = base_time
    updated_at = base_time + timedelta(hours=draw(st.integers(min_value=0, max_value=24)))
    
    # Generate messages with simpler timestamp strategy
    message_count = draw(st.integers(min_value=1, max_value=10))
    messages = []
    
    for i in range(message_count):
        message_time = created_at + timedelta(minutes=i * 10)  # Simple incremental timestamps
        messages.append(Message(
            role=draw(st.sampled_from(['user', 'assistant'])),
            content=draw(st.text(min_size=1, max_size=500)),
            timestamp=message_time,
            metadata=draw(st.dictionaries(st.text(max_size=10), st.text(max_size=10), max_size=3))
        ))
    
    return Conversation(
        id=conv_id,
        title=title,
        created_at=created_at,
        updated_at=updated_at,
        messages=messages
    )


@st.composite
def project_brief_strategy(draw):
    """Generate a random project brief."""
    name = draw(st.text(min_size=1, max_size=50))
    description = draw(st.text(min_size=1, max_size=200))
    
    tech_stack = draw(st.lists(
        st.sampled_from(['Python', 'JavaScript', 'TypeScript', 'React', 'FastAPI', 'Node.js', 'PostgreSQL', 'MongoDB']),
        min_size=0,
        max_size=5,
        unique=True
    ))
    
    key_challenges = draw(st.lists(
        st.text(min_size=1, max_size=100),
        min_size=0,
        max_size=3
    ))
    
    current_status = draw(st.sampled_from(['Planning', 'In development', 'Testing', 'Production', 'Maintenance']))
    
    # Use fixed base time for consistent generation
    last_discussed = datetime(2023, 1, 1) + timedelta(days=draw(st.integers(min_value=1, max_value=365)))
    
    relevance_score = draw(st.floats(min_value=0.0, max_value=1.0))
    
    return ProjectBrief(
        name=name,
        description=description,
        tech_stack=tech_stack,
        key_challenges=key_challenges,
        current_status=current_status,
        last_discussed=last_discussed,
        relevance_score=relevance_score
    )


@st.composite
def technical_context_strategy(draw):
    """Generate a random technical context."""
    languages = draw(st.lists(
        st.sampled_from(['Python', 'JavaScript', 'TypeScript', 'Java', 'C++', 'Go', 'Rust']),
        min_size=0,
        max_size=5,
        unique=True
    ))
    
    frameworks = draw(st.lists(
        st.sampled_from(['React', 'Vue', 'Angular', 'FastAPI', 'Django', 'Express', 'Spring']),
        min_size=0,
        max_size=5,
        unique=True
    ))
    
    tools = draw(st.lists(
        st.sampled_from(['Git', 'Docker', 'VS Code', 'IntelliJ', 'Postman', 'Jenkins']),
        min_size=0,
        max_size=5,
        unique=True
    ))
    
    domains = draw(st.lists(
        st.sampled_from(['web development', 'mobile development', 'data science', 'machine learning', 'DevOps']),
        min_size=0,
        max_size=3,
        unique=True
    ))
    
    return TechnicalContext(
        languages=languages,
        frameworks=frameworks,
        tools=tools,
        domains=domains
    )


@st.composite
def context_pack_strategy(draw):
    """Generate a random universal context pack."""
    version = draw(st.text(min_size=1, max_size=10))
    # Use fixed base time for consistent generation
    created_at = datetime(2023, 1, 1) + timedelta(days=draw(st.integers(min_value=1, max_value=30)))
    source_platform = draw(st.sampled_from(['chatgpt', 'claude', 'gemini']))
    
    projects = draw(st.lists(project_brief_strategy(), min_size=0, max_size=10))
    technical_context = draw(technical_context_strategy())
    
    return UniversalContextPack(
        version=version,
        created_at=created_at,
        source_platform=source_platform,
        user_profile=UserProfile(),
        projects=projects,
        preferences=UserPreferences(),
        technical_context=technical_context
    )


@st.composite
def filter_config_strategy(draw):
    """Generate a random filter configuration."""
    excluded_conversation_ids = draw(st.lists(
        st.text(min_size=1, max_size=20),
        min_size=0,
        max_size=5,
        unique=True
    ))
    
    excluded_topics = draw(st.lists(
        st.sampled_from(['Python', 'JavaScript', 'React', 'web development', 'API', 'database']),
        min_size=0,
        max_size=3,
        unique=True
    ))
    
    # Optional date range with fixed base time
    date_range = None
    if draw(st.booleans()):
        base_date = datetime(2023, 1, 1)
        start_days = draw(st.integers(min_value=1, max_value=300))
        end_days = draw(st.integers(min_value=start_days + 1, max_value=365))
        
        start_date = base_date + timedelta(days=start_days)
        end_date = base_date + timedelta(days=end_days)
        date_range = (start_date, end_date)
    
    min_relevance_score = draw(st.floats(min_value=0.0, max_value=1.0))
    
    return FilterConfig(
        excluded_conversation_ids=excluded_conversation_ids,
        excluded_topics=excluded_topics,
        date_range=date_range,
        min_relevance_score=min_relevance_score
    )


class TestFilterProperties:
    """Property-based tests for FilterEngine."""
    
    def _create_filter_engine(self):
        """Create a FilterEngine instance with temporary preferences file."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as f:
            temp_file = f.name
        return FilterEngine(preferences_file=temp_file), temp_file
    
    @given(st.lists(conversation_strategy(), min_size=1, max_size=20), filter_config_strategy())
    @settings(max_examples=100)
    def test_conversation_exclusion_property(self, conversations, filters):
        """
        Feature: llm-context-exporter, Property 14: Conversation exclusion
        
        For any FilterConfig with excluded conversation IDs, those conversations 
        should not appear in the filtered conversation list.
        """
        filter_engine, temp_file = self._create_filter_engine()
        
        try:
            # Apply conversation exclusions
            filtered_conversations = filter_engine.apply_conversation_exclusions(conversations, filters)
            
            # Property: No excluded conversation should appear in the filtered list
            excluded_ids_set = set(filters.excluded_conversation_ids)
            filtered_ids_set = set(conv.id for conv in filtered_conversations)
            
            # The intersection should be empty (no excluded IDs in filtered results)
            assert excluded_ids_set.isdisjoint(filtered_ids_set), \
                f"Excluded conversations {excluded_ids_set & filtered_ids_set} found in filtered results"
            
            # Property: All non-excluded conversations should be present
            original_ids_set = set(conv.id for conv in conversations)
            expected_ids_set = original_ids_set - excluded_ids_set
            
            assert filtered_ids_set == expected_ids_set, \
                f"Expected {expected_ids_set}, but got {filtered_ids_set}"
        
        finally:
            # Cleanup
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    @given(context_pack_strategy(), filter_config_strategy())
    @settings(max_examples=100)
    def test_topic_exclusion_property(self, context, filters):
        """
        Feature: llm-context-exporter, Property 15: Topic exclusion
        
        For any FilterConfig with excluded topics, projects and content related 
        to those topics should not appear in the filtered output.
        """
        filter_engine, temp_file = self._create_filter_engine()
        
        try:
            # Apply filters
            filtered_context = filter_engine.apply_filters(context, filters)
            
            # Property: No project should contain excluded topics in its name or tech stack
            for project in filtered_context.projects:
                for excluded_topic in filters.excluded_topics:
                    # Check project name doesn't match excluded topic
                    assert not filter_engine._is_topic_excluded(project.name, filters.excluded_topics), \
                        f"Project '{project.name}' should be excluded due to topic '{excluded_topic}'"
                    
                    # Check tech stack doesn't contain excluded topics
                    for tech in project.tech_stack:
                        assert not filter_engine._is_topic_excluded(tech, filters.excluded_topics), \
                            f"Project '{project.name}' should be excluded due to tech '{tech}' matching topic '{excluded_topic}'"
            
            # Property: Technical context should not contain excluded topics
            for excluded_topic in filters.excluded_topics:
                # Check languages
                for language in filtered_context.technical_context.languages:
                    assert not filter_engine._is_topic_excluded(language, filters.excluded_topics), \
                        f"Language '{language}' should be excluded due to topic '{excluded_topic}'"
            
            # Check frameworks
            for framework in filtered_context.technical_context.frameworks:
                assert not filter_engine._is_topic_excluded(framework, filters.excluded_topics), \
                    f"Framework '{framework}' should be excluded due to topic '{excluded_topic}'"
            
            # Check tools
            for tool in filtered_context.technical_context.tools:
                assert not filter_engine._is_topic_excluded(tool, filters.excluded_topics), \
                    f"Tool '{tool}' should be excluded due to topic '{excluded_topic}'"
            
            # Check domains
            for domain in filtered_context.technical_context.domains:
                assert not filter_engine._is_topic_excluded(domain, filters.excluded_topics), \
                    f"Domain '{domain}' should be excluded due to topic '{excluded_topic}'"
        
        finally:
            # Cleanup
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    @given(filter_config_strategy())
    @settings(max_examples=100)
    def test_filter_persistence_property(self, filters):
        """
        Feature: llm-context-exporter, Property 16: Filter persistence
        
        For any saved FilterConfig, loading the preferences in a subsequent run 
        should produce the same filter settings.
        """
        filter_engine, temp_file = self._create_filter_engine()
        
        try:
            # Save the filter preferences
            filter_engine.save_filter_preferences(filters)
            
            # Load the filter preferences
            loaded_filters = filter_engine.load_filter_preferences()
            
            # Property: All filter settings should be preserved
            assert loaded_filters.excluded_conversation_ids == filters.excluded_conversation_ids, \
                "Excluded conversation IDs not preserved"
            
            assert loaded_filters.excluded_topics == filters.excluded_topics, \
                "Excluded topics not preserved"
            
            assert loaded_filters.min_relevance_score == filters.min_relevance_score, \
                "Minimum relevance score not preserved"
            
            # Date range requires special handling due to serialization
            if filters.date_range is None:
                assert loaded_filters.date_range is None, "Date range should be None"
            else:
                assert loaded_filters.date_range is not None, "Date range should not be None"
                original_start, original_end = filters.date_range
                loaded_start, loaded_end = loaded_filters.date_range
                
                # Allow for small differences due to serialization precision
                assert abs((original_start - loaded_start).total_seconds()) < 1, \
                    f"Start date not preserved: {original_start} vs {loaded_start}"
                assert abs((original_end - loaded_end).total_seconds()) < 1, \
                    f"End date not preserved: {original_end} vs {loaded_end}"
        
        finally:
            # Cleanup
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    @given(context_pack_strategy(), filter_config_strategy())
    @settings(max_examples=50)
    def test_filter_coherence_property(self, context, filters):
        """
        Property: Filtering should preserve context coherence.
        
        The filtered context should maintain structural integrity and 
        essential user information.
        """
        filter_engine, temp_file = self._create_filter_engine()
        
        try:
            # Apply filters
            filtered_context = filter_engine.apply_filters(context, filters)
            
            # Property: Basic structure should be preserved
            assert filtered_context.version == context.version
            assert filtered_context.created_at == context.created_at
            assert filtered_context.source_platform == context.source_platform
            
            # Property: User profile and preferences should not be filtered
            assert filtered_context.user_profile == context.user_profile
            assert filtered_context.preferences == context.preferences
            
            # Property: Metadata should indicate filtering was applied
            assert filtered_context.metadata.get("filtered") is True
            assert "filter_applied_at" in filtered_context.metadata
            assert "original_project_count" in filtered_context.metadata
            assert "filtered_project_count" in filtered_context.metadata
        
        finally:
            # Cleanup
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    @given(context_pack_strategy(), st.floats(min_value=0.0, max_value=1.0))
    @settings(max_examples=50)
    def test_relevance_score_filtering_property(self, context, min_score):
        """
        Property: Relevance score filtering should only include projects 
        with scores >= minimum threshold.
        """
        filter_engine, temp_file = self._create_filter_engine()
        
        try:
            filters = FilterConfig(min_relevance_score=min_score)
            filtered_context = filter_engine.apply_filters(context, filters)
            
            # Property: All filtered projects should have relevance >= min_score
            for project in filtered_context.projects:
                assert project.relevance_score >= min_score, \
                    f"Project '{project.name}' has relevance {project.relevance_score} < {min_score}"
            
            # Property: All projects with relevance >= min_score should be included
            # (unless excluded by other filters)
            expected_projects = [p for p in context.projects if p.relevance_score >= min_score]
            assert len(filtered_context.projects) == len(expected_projects), \
                f"Expected {len(expected_projects)} projects, got {len(filtered_context.projects)}"
        
        finally:
            # Cleanup
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    @given(context_pack_strategy())
    @settings(max_examples=50)
    def test_date_range_filtering_property(self, context):
        """
        Property: Date range filtering should only include projects 
        discussed within the specified range.
        """
        assume(len(context.projects) > 0)
        filter_engine, temp_file = self._create_filter_engine()
        
        try:
            # Create a date range that includes some projects
            all_dates = [p.last_discussed for p in context.projects]
            min_date = min(all_dates)
            max_date = max(all_dates)
            
            # Create a range that excludes some projects
            mid_date = min_date + (max_date - min_date) / 2
            
            filters = FilterConfig(date_range=(mid_date, max_date))
            filtered_context = filter_engine.apply_filters(context, filters)
            
            # Property: All filtered projects should be within date range
            for project in filtered_context.projects:
                assert mid_date <= project.last_discussed <= max_date, \
                    f"Project '{project.name}' discussed at {project.last_discussed} is outside range [{mid_date}, {max_date}]"
            
            # Property: All projects within range should be included
            expected_count = sum(1 for p in context.projects if mid_date <= p.last_discussed <= max_date)
            assert len(filtered_context.projects) == expected_count, \
                f"Expected {expected_count} projects in date range, got {len(filtered_context.projects)}"
        
        finally:
            # Cleanup
            if os.path.exists(temp_file):
                os.unlink(temp_file)


# Run the property-based tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])