"""
Filter and selection engine for controlling what context is included.

This module provides functionality for users to selectively include/exclude
conversations, topics, and other content from their context packages.
"""

from typing import List, Dict, Any
from datetime import datetime
import json
import os

from .models import UniversalContextPack, FilterConfig, Conversation, ProjectBrief, TechnicalContext


class FilterableItem:
    """Represents an item that can be filtered (conversation, project, etc.)."""
    
    def __init__(self, item_id: str, item_type: str, title: str, description: str, metadata: Dict[str, Any] = None):
        self.item_id = item_id
        self.item_type = item_type  # 'conversation', 'project', 'topic'
        self.title = title
        self.description = description
        self.metadata = metadata or {}


class FilterEngine:
    """
    Manages filtering and selection of context content.
    
    Allows users to exclude specific conversations, projects, or topics
    from their exported context while maintaining coherence.
    """
    
    def __init__(self, preferences_file: str = None):
        """
        Initialize the filter engine.
        
        Args:
            preferences_file: Path to save/load filter preferences
        """
        self.preferences_file = preferences_file or os.path.expanduser("~/.llm_context_exporter_filters.json")
    
    def apply_filters(self, context: UniversalContextPack, filters: FilterConfig) -> UniversalContextPack:
        """
        Apply user-defined filters to context pack.
        
        Args:
            context: Original context pack
            filters: Filter configuration
            
        Returns:
            Filtered context pack
        """
        # Filter projects based on various criteria
        filtered_projects = self._filter_projects(context.projects, filters)
        
        # Filter technical context based on excluded topics
        filtered_technical_context = self._filter_technical_context(context.technical_context, filters)
        
        # Create filtered context pack
        filtered_context = UniversalContextPack(
            version=context.version,
            created_at=context.created_at,
            source_platform=context.source_platform,
            user_profile=context.user_profile,  # Profile is not filtered
            projects=filtered_projects,
            preferences=context.preferences,  # Preferences are not filtered
            technical_context=filtered_technical_context,
            metadata={
                **context.metadata,
                "filtered": True,
                "filter_applied_at": datetime.now().isoformat(),
                "original_project_count": len(context.projects),
                "filtered_project_count": len(filtered_projects),
                "excluded_conversation_ids": filters.excluded_conversation_ids,
                "excluded_topics": filters.excluded_topics,
                "date_range": [
                    filters.date_range[0].isoformat() if filters.date_range and filters.date_range[0] else None,
                    filters.date_range[1].isoformat() if filters.date_range and filters.date_range[1] else None
                ] if filters.date_range else None,
                "min_relevance_score": filters.min_relevance_score
            }
        )
        
        return filtered_context
    
    def get_filterable_items(self, context: UniversalContextPack) -> List[FilterableItem]:
        """
        Return list of items that can be filtered.
        
        Args:
            context: Context pack to analyze
            
        Returns:
            List of filterable items with metadata
        """
        items = []
        
        # Add projects as filterable items
        for project in context.projects:
            items.append(FilterableItem(
                item_id=f"project_{project.name}",
                item_type="project",
                title=project.name,
                description=project.description,
                metadata={
                    "tech_stack": project.tech_stack,
                    "last_discussed": project.last_discussed.isoformat(),
                    "relevance_score": project.relevance_score,
                    "current_status": project.current_status
                }
            ))
        
        # Add technical domains as filterable topics
        for domain in context.technical_context.domains:
            items.append(FilterableItem(
                item_id=f"domain_{domain}",
                item_type="topic",
                title=domain.title(),
                description=f"Technical domain: {domain}",
                metadata={"type": "domain"}
            ))
        
        # Add programming languages as filterable topics
        for language in context.technical_context.languages:
            items.append(FilterableItem(
                item_id=f"language_{language}",
                item_type="topic", 
                title=language.title(),
                description=f"Programming language: {language}",
                metadata={"type": "language"}
            ))
        
        # Add frameworks as filterable topics
        for framework in context.technical_context.frameworks:
            items.append(FilterableItem(
                item_id=f"framework_{framework}",
                item_type="topic",
                title=framework,
                description=f"Framework/Library: {framework}",
                metadata={"type": "framework"}
            ))
        
        # Add tools as filterable topics
        for tool in context.technical_context.tools:
            items.append(FilterableItem(
                item_id=f"tool_{tool}",
                item_type="topic",
                title=tool,
                description=f"Development tool: {tool}",
                metadata={"type": "tool"}
            ))
        
        return items
    
    def get_filterable_conversations(self, conversations: List[Conversation]) -> List[FilterableItem]:
        """
        Return list of conversations that can be filtered.
        
        This method is used during the parsing phase when we have access
        to raw conversation data.
        
        Args:
            conversations: List of conversations to analyze
            
        Returns:
            List of filterable conversation items
        """
        items = []
        
        for conversation in conversations:
            # Calculate some basic metadata
            message_count = len(conversation.messages)
            duration_days = (conversation.updated_at - conversation.created_at).days
            
            items.append(FilterableItem(
                item_id=f"conversation_{conversation.id}",
                item_type="conversation",
                title=conversation.title,
                description=f"Conversation with {message_count} messages",
                metadata={
                    "id": conversation.id,
                    "created_at": conversation.created_at.isoformat(),
                    "updated_at": conversation.updated_at.isoformat(),
                    "message_count": message_count,
                    "duration_days": duration_days
                }
            ))
        
        return items
    
    def save_filter_preferences(self, filters: FilterConfig) -> None:
        """
        Persist filter preferences for future runs.
        
        Args:
            filters: Filter configuration to save
        """
        try:
            filter_data = {
                "excluded_conversation_ids": filters.excluded_conversation_ids,
                "excluded_topics": filters.excluded_topics,
                "date_range": [
                    filters.date_range[0].isoformat() if filters.date_range and filters.date_range[0] else None,
                    filters.date_range[1].isoformat() if filters.date_range and filters.date_range[1] else None
                ] if filters.date_range else None,
                "min_relevance_score": filters.min_relevance_score,
                "saved_at": datetime.now().isoformat()
            }
            
            os.makedirs(os.path.dirname(self.preferences_file), exist_ok=True)
            with open(self.preferences_file, 'w') as f:
                json.dump(filter_data, f, indent=2)
                
        except Exception as e:
            # Don't fail the entire operation if preferences can't be saved
            print(f"Warning: Could not save filter preferences: {e}")
    
    def load_filter_preferences(self) -> FilterConfig:
        """
        Load previously saved filter preferences.
        
        Returns:
            FilterConfig with saved preferences, or empty config if none exist
        """
        try:
            if not os.path.exists(self.preferences_file):
                return FilterConfig()
            
            with open(self.preferences_file, 'r') as f:
                filter_data = json.load(f)
            
            date_range = None
            if filter_data.get("date_range") and filter_data["date_range"][0] and filter_data["date_range"][1]:
                date_range = (
                    datetime.fromisoformat(filter_data["date_range"][0]),
                    datetime.fromisoformat(filter_data["date_range"][1])
                )
            
            return FilterConfig(
                excluded_conversation_ids=filter_data.get("excluded_conversation_ids", []),
                excluded_topics=filter_data.get("excluded_topics", []),
                date_range=date_range,
                min_relevance_score=filter_data.get("min_relevance_score", 0.0)
            )
            
        except Exception as e:
            print(f"Warning: Could not load filter preferences: {e}")
            return FilterConfig()
    
    def create_filter_from_exclusions(self, excluded_items: List[str]) -> FilterConfig:
        """
        Create a filter configuration from a list of excluded item IDs.
        
        Args:
            excluded_items: List of item IDs to exclude (from get_filterable_items)
            
        Returns:
            FilterConfig with appropriate exclusions
        """
        excluded_conversations = []
        excluded_topics = []
        
        for item_id in excluded_items:
            if item_id.startswith("conversation_"):
                # Extract conversation ID
                conversation_id = item_id.replace("conversation_", "")
                excluded_conversations.append(conversation_id)
            elif item_id.startswith("project_"):
                # Extract project name as topic
                project_name = item_id.replace("project_", "")
                excluded_topics.append(project_name)
            elif item_id.startswith("domain_") or item_id.startswith("language_") or item_id.startswith("framework_") or item_id.startswith("tool_"):
                # Extract technical topic
                topic = item_id.split("_", 1)[1]
                excluded_topics.append(topic)
        
        return FilterConfig(
            excluded_conversation_ids=excluded_conversations,
            excluded_topics=excluded_topics
        )
    
    def apply_conversation_exclusions(self, conversations: List[Conversation], filters: FilterConfig) -> List[Conversation]:
        """
        Apply conversation exclusion filters to a list of conversations.
        
        This method is used during the parsing/extraction phase when we have
        access to the raw conversation data.
        
        Args:
            conversations: List of conversations to filter
            filters: Filter configuration
            
        Returns:
            Filtered list of conversations
        """
        if not filters.excluded_conversation_ids:
            return conversations
        
        filtered_conversations = []
        excluded_ids_set = set(filters.excluded_conversation_ids)
        
        for conversation in conversations:
            if conversation.id not in excluded_ids_set:
                filtered_conversations.append(conversation)
        
        return filtered_conversations
    
    def _filter_projects(self, projects: List[ProjectBrief], filters: FilterConfig) -> List[ProjectBrief]:
        """Filter projects based on filter configuration."""
        filtered_projects = []
        
        for project in projects:
            # Check if project should be excluded
            if self._should_exclude_project(project, filters):
                continue
            
            # Check relevance score threshold
            if project.relevance_score < filters.min_relevance_score:
                continue
            
            # Check date range
            if filters.date_range:
                start_date, end_date = filters.date_range
                if not (start_date <= project.last_discussed <= end_date):
                    continue
            
            filtered_projects.append(project)
        
        return filtered_projects
    
    def _filter_technical_context(self, technical_context: TechnicalContext, filters: FilterConfig) -> TechnicalContext:
        """Filter technical context based on excluded topics."""
        
        # Create lists excluding filtered topics
        filtered_languages = [
            lang for lang in technical_context.languages
            if not self._is_topic_excluded(lang, filters.excluded_topics)
        ]
        
        filtered_frameworks = [
            fw for fw in technical_context.frameworks
            if not self._is_topic_excluded(fw, filters.excluded_topics)
        ]
        
        filtered_tools = [
            tool for tool in technical_context.tools
            if not self._is_topic_excluded(tool, filters.excluded_topics)
        ]
        
        filtered_domains = [
            domain for domain in technical_context.domains
            if not self._is_topic_excluded(domain, filters.excluded_topics)
        ]
        
        return TechnicalContext(
            languages=filtered_languages,
            frameworks=filtered_frameworks,
            tools=filtered_tools,
            domains=filtered_domains
        )
    
    def _should_exclude_project(self, project: ProjectBrief, filters: FilterConfig) -> bool:
        """Check if a project should be excluded based on filters."""
        # Check if project name is in excluded topics
        if self._is_topic_excluded(project.name, filters.excluded_topics):
            return True
        
        # Check if any of the project's tech stack is excluded
        for tech in project.tech_stack:
            if self._is_topic_excluded(tech, filters.excluded_topics):
                return True
        
        # Check if any key challenges mention excluded topics
        for challenge in project.key_challenges:
            if self._is_topic_excluded(challenge, filters.excluded_topics):
                return True
        
        return False
    
    def _is_topic_excluded(self, item: str, excluded_topics: List[str]) -> bool:
        """Check if an item matches any excluded topic (case-insensitive)."""
        item_lower = item.lower()
        for excluded_topic in excluded_topics:
            excluded_lower = excluded_topic.lower()
            # Check for exact match or if the excluded topic is contained in the item
            if excluded_lower == item_lower or excluded_lower in item_lower:
                return True
        return False
    
    def get_filter_summary(self, original_context: UniversalContextPack, filtered_context: UniversalContextPack) -> Dict[str, Any]:
        """
        Generate a summary of what was filtered out.
        
        Args:
            original_context: Original context before filtering
            filtered_context: Context after filtering
            
        Returns:
            Dictionary with filtering statistics
        """
        return {
            "projects_removed": len(original_context.projects) - len(filtered_context.projects),
            "projects_remaining": len(filtered_context.projects),
            "removed_project_names": [
                p.name for p in original_context.projects 
                if p.name not in [fp.name for fp in filtered_context.projects]
            ],
            "filter_applied_at": filtered_context.metadata.get("filter_applied_at"),
            "coherence_maintained": len(filtered_context.projects) > 0  # Simple coherence check
        }
    
    def get_filterable_conversations(self, conversations: List[Conversation]) -> List[FilterableItem]:
        """
        Return list of conversations that can be filtered.
        
        This method is used during the parsing phase when we have access
        to raw conversation data.
        
        Args:
            conversations: List of conversations to analyze
            
        Returns:
            List of filterable conversation items
        """
        items = []
        
        for conversation in conversations:
            # Calculate some basic metadata
            message_count = len(conversation.messages)
            duration_days = (conversation.updated_at - conversation.created_at).days
            
            items.append(FilterableItem(
                item_id=f"conversation_{conversation.id}",
                item_type="conversation",
                title=conversation.title,
                description=f"Conversation with {message_count} messages",
                metadata={
                    "id": conversation.id,
                    "created_at": conversation.created_at.isoformat(),
                    "updated_at": conversation.updated_at.isoformat(),
                    "message_count": message_count,
                    "duration_days": duration_days
                }
            ))
        
        return items
    
    def create_date_range_filter(self, start_date: datetime, end_date: datetime) -> FilterConfig:
        """
        Create a filter configuration with a date range.
        
        Args:
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)
            
        Returns:
            FilterConfig with date range set
        """
        if start_date >= end_date:
            raise ValueError("Start date must be before end date")
        
        return FilterConfig(date_range=(start_date, end_date))
    
    def create_relevance_filter(self, min_score: float) -> FilterConfig:
        """
        Create a filter configuration with minimum relevance score.
        
        Args:
            min_score: Minimum relevance score (0.0 to 1.0)
            
        Returns:
            FilterConfig with relevance threshold set
        """
        if not 0.0 <= min_score <= 1.0:
            raise ValueError("Relevance score must be between 0.0 and 1.0")
        
        return FilterConfig(min_relevance_score=min_score)