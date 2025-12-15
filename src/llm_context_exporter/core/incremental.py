"""
Incremental update functionality for LLM Context Exporter.

This module handles detecting new conversations, merging contexts,
generating delta packages, and maintaining version history.
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Set
from pathlib import Path
import hashlib

from .models import (
    Conversation,
    UniversalContextPack,
    ParsedExport,
    ProjectBrief,
    UserProfile,
    UserPreferences,
    TechnicalContext
)


class IncrementalUpdater:
    """
    Handles incremental updates to context packages.
    
    Provides functionality to:
    - Detect new conversations since last export
    - Merge new context with existing context
    - Generate delta packages containing only new information
    - Maintain version history
    """
    
    def __init__(self):
        """Initialize the incremental updater."""
        self.version_history_file = "version_history.json"
    
    def detect_new_conversations(
        self, 
        current_export: ParsedExport, 
        previous_export: ParsedExport
    ) -> List[Conversation]:
        """
        Identify conversations added since the last export.
        
        Args:
            current_export: The new export data
            previous_export: The previous export data
            
        Returns:
            List of conversations that are new or updated
        """
        # Create sets of conversation IDs for comparison
        previous_conv_ids = {conv.id for conv in previous_export.conversations}
        current_conversations = current_export.conversations
        
        new_conversations = []
        
        for conv in current_conversations:
            if conv.id not in previous_conv_ids:
                # Completely new conversation
                new_conversations.append(conv)
            else:
                # Check if conversation was updated
                previous_conv = next(
                    (c for c in previous_export.conversations if c.id == conv.id), 
                    None
                )
                if previous_conv and self._conversation_updated(conv, previous_conv):
                    new_conversations.append(conv)
        
        return new_conversations
    
    def merge_contexts(
        self, 
        existing_context: UniversalContextPack, 
        new_context: UniversalContextPack
    ) -> UniversalContextPack:
        """
        Merge new context with existing context, resolving conflicts.
        
        Args:
            existing_context: The existing context pack
            new_context: The new context pack to merge
            
        Returns:
            Merged UniversalContextPack with conflict resolution
        """
        # Create new version number
        existing_version_parts = existing_context.version.split('.')
        major, minor = int(existing_version_parts[0]), int(existing_version_parts[1])
        new_version = f"{major}.{minor + 1}"
        
        # Merge user profile
        merged_profile = self._merge_user_profiles(
            existing_context.user_profile, 
            new_context.user_profile
        )
        
        # Merge projects (with conflict resolution)
        merged_projects = self._merge_projects(
            existing_context.projects, 
            new_context.projects
        )
        
        # Merge preferences
        merged_preferences = self._merge_preferences(
            existing_context.preferences, 
            new_context.preferences
        )
        
        # Merge technical context
        merged_technical = self._merge_technical_context(
            existing_context.technical_context, 
            new_context.technical_context
        )
        
        # Create merged metadata
        merged_metadata = {
            **existing_context.metadata,
            **new_context.metadata,
            "merge_date": datetime.now().isoformat(),
            "previous_version": existing_context.version,
            "merge_source": "incremental_update"
        }
        
        return UniversalContextPack(
            version=new_version,
            created_at=existing_context.created_at,  # Keep original creation date
            source_platform=existing_context.source_platform,
            user_profile=merged_profile,
            projects=merged_projects,
            preferences=merged_preferences,
            technical_context=merged_technical,
            metadata=merged_metadata
        )
    
    def generate_delta_package(
        self, 
        existing_context: UniversalContextPack, 
        new_context: UniversalContextPack
    ) -> UniversalContextPack:
        """
        Generate a delta package containing only new information.
        
        Args:
            existing_context: The existing context pack
            new_context: The new context pack
            
        Returns:
            Delta UniversalContextPack with only new information
        """
        # Find new projects
        existing_project_names = {p.name.lower() for p in existing_context.projects}
        new_projects = [
            p for p in new_context.projects 
            if p.name.lower() not in existing_project_names
        ]
        
        # Find new technical items
        existing_languages = set(existing_context.technical_context.languages)
        existing_frameworks = set(existing_context.technical_context.frameworks)
        existing_tools = set(existing_context.technical_context.tools)
        existing_domains = set(existing_context.technical_context.domains)
        
        new_languages = [
            lang for lang in new_context.technical_context.languages 
            if lang not in existing_languages
        ]
        new_frameworks = [
            fw for fw in new_context.technical_context.frameworks 
            if fw not in existing_frameworks
        ]
        new_tools = [
            tool for tool in new_context.technical_context.tools 
            if tool not in existing_tools
        ]
        new_domains = [
            domain for domain in new_context.technical_context.domains 
            if domain not in existing_domains
        ]
        
        # Find new preferences
        new_preferred_tools = [
            tool for tool in new_context.preferences.preferred_tools
            if tool not in existing_context.preferences.preferred_tools
        ]
        
        # Create delta technical context
        delta_technical = TechnicalContext(
            languages=new_languages,
            frameworks=new_frameworks,
            tools=new_tools,
            domains=new_domains
        )
        
        # Create delta preferences (only new items)
        delta_preferences = UserPreferences(
            coding_style={
                k: v for k, v in new_context.preferences.coding_style.items()
                if k not in existing_context.preferences.coding_style
            },
            communication_style=new_context.preferences.communication_style,
            preferred_tools=new_preferred_tools,
            work_patterns={
                k: v for k, v in new_context.preferences.work_patterns.items()
                if k not in existing_context.preferences.work_patterns
            }
        )
        
        # Create delta user profile (only new expertise areas)
        new_expertise = [
            area for area in new_context.user_profile.expertise_areas
            if area not in existing_context.user_profile.expertise_areas
        ]
        
        delta_profile = UserProfile(
            role=new_context.user_profile.role,  # Keep current role
            expertise_areas=new_expertise,
            background_summary=new_context.user_profile.background_summary
        )
        
        return UniversalContextPack(
            version=f"delta-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            created_at=datetime.now(),
            source_platform=new_context.source_platform,
            user_profile=delta_profile,
            projects=new_projects,
            preferences=delta_preferences,
            technical_context=delta_technical,
            metadata={
                "delta_from_version": existing_context.version,
                "delta_to_version": new_context.version,
                "delta_created": datetime.now().isoformat(),
                "new_projects_count": len(new_projects),
                "new_languages_count": len(new_languages),
                "new_frameworks_count": len(new_frameworks)
            }
        )
    
    def save_version_history(
        self, 
        context: UniversalContextPack, 
        output_dir: str
    ) -> None:
        """
        Maintain version history of context packages.
        
        Args:
            context: The context pack to record
            output_dir: Directory to save version history
        """
        history_file = Path(output_dir) / self.version_history_file
        
        # Load existing history
        history = []
        if history_file.exists():
            try:
                with open(history_file, 'r') as f:
                    history = json.load(f)
            except (json.JSONDecodeError, IOError):
                # If file is corrupted, start fresh
                history = []
        
        # Create new history entry
        new_entry = {
            "version": context.version,
            "created_at": context.created_at.isoformat(),
            "source_platform": context.source_platform,
            "projects_count": len(context.projects),
            "languages_count": len(context.technical_context.languages),
            "frameworks_count": len(context.technical_context.frameworks),
            "metadata": context.metadata
        }
        
        # Add to history (maintain chronological order)
        history.append(new_entry)
        
        # Sort by version to ensure monotonic ordering
        history.sort(key=lambda x: self._version_to_tuple(x["version"]))
        
        # Save updated history
        os.makedirs(output_dir, exist_ok=True)
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2, default=str)
    
    def load_previous_context(self, context_path: str) -> Optional[UniversalContextPack]:
        """
        Load a previous context pack from file.
        
        Args:
            context_path: Path to the previous context pack JSON file
            
        Returns:
            UniversalContextPack if found and valid, None otherwise
        """
        if not os.path.exists(context_path):
            return None
        
        try:
            with open(context_path, 'r') as f:
                data = json.load(f)
            
            # Convert datetime strings back to datetime objects
            data['created_at'] = datetime.fromisoformat(data['created_at'])
            
            # Convert projects
            projects = []
            for p_data in data.get('projects', []):
                p_data['last_discussed'] = datetime.fromisoformat(p_data['last_discussed'])
                projects.append(ProjectBrief(**p_data))
            
            # Create context pack
            return UniversalContextPack(
                version=data['version'],
                created_at=data['created_at'],
                source_platform=data['source_platform'],
                user_profile=UserProfile(**data.get('user_profile', {})),
                projects=projects,
                preferences=UserPreferences(**data.get('preferences', {})),
                technical_context=TechnicalContext(**data.get('technical_context', {})),
                metadata=data.get('metadata', {})
            )
        
        except (json.JSONDecodeError, KeyError, ValueError, TypeError) as e:
            print(f"Error loading previous context: {e}")
            return None
    
    def save_context_pack(self, context: UniversalContextPack, output_path: str) -> None:
        """
        Save a context pack to JSON file.
        
        Args:
            context: The context pack to save
            output_path: Path where to save the context pack
        """
        # Convert to dictionary for JSON serialization
        data = {
            "version": context.version,
            "created_at": context.created_at.isoformat(),
            "source_platform": context.source_platform,
            "user_profile": {
                "role": context.user_profile.role,
                "expertise_areas": context.user_profile.expertise_areas,
                "background_summary": context.user_profile.background_summary
            },
            "projects": [
                {
                    "name": p.name,
                    "description": p.description,
                    "tech_stack": p.tech_stack,
                    "key_challenges": p.key_challenges,
                    "current_status": p.current_status,
                    "last_discussed": p.last_discussed.isoformat(),
                    "relevance_score": p.relevance_score
                }
                for p in context.projects
            ],
            "preferences": {
                "coding_style": context.preferences.coding_style,
                "communication_style": context.preferences.communication_style,
                "preferred_tools": context.preferences.preferred_tools,
                "work_patterns": context.preferences.work_patterns
            },
            "technical_context": {
                "languages": context.technical_context.languages,
                "frameworks": context.technical_context.frameworks,
                "tools": context.technical_context.tools,
                "domains": context.technical_context.domains
            },
            "metadata": context.metadata
        }
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save to file
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def _conversation_updated(self, current: Conversation, previous: Conversation) -> bool:
        """Check if a conversation has been updated since the previous export."""
        # Compare update timestamps
        if current.updated_at > previous.updated_at:
            return True
        
        # Compare message counts
        if len(current.messages) != len(previous.messages):
            return True
        
        # Compare message content hashes (for efficiency)
        current_hash = self._conversation_content_hash(current)
        previous_hash = self._conversation_content_hash(previous)
        
        return current_hash != previous_hash
    
    def _conversation_content_hash(self, conversation: Conversation) -> str:
        """Generate a hash of conversation content for comparison."""
        content = f"{conversation.title}|{len(conversation.messages)}"
        for msg in conversation.messages:
            content += f"|{msg.role}:{msg.content[:100]}"  # First 100 chars for efficiency
        
        return hashlib.md5(content.encode()).hexdigest()
    
    def _merge_user_profiles(self, existing: UserProfile, new: UserProfile) -> UserProfile:
        """Merge two user profiles, preferring newer information."""
        # Use newer role if available
        role = new.role if new.role else existing.role
        
        # Merge expertise areas (union)
        expertise_areas = list(set(existing.expertise_areas + new.expertise_areas))
        
        # Use newer background summary if it's more detailed
        background_summary = (
            new.background_summary 
            if len(new.background_summary) > len(existing.background_summary)
            else existing.background_summary
        )
        
        return UserProfile(
            role=role,
            expertise_areas=expertise_areas,
            background_summary=background_summary
        )
    
    def _merge_projects(self, existing: List[ProjectBrief], new: List[ProjectBrief]) -> List[ProjectBrief]:
        """Merge project lists, resolving conflicts by project name."""
        merged = {}
        
        # Add existing projects
        for project in existing:
            merged[project.name.lower()] = project
        
        # Add or update with new projects
        for project in new:
            key = project.name.lower()
            if key in merged:
                # Merge existing project with new information
                existing_project = merged[key]
                merged[key] = self._merge_single_project(existing_project, project)
            else:
                # Add new project
                merged[key] = project
        
        # Return sorted by relevance score
        projects = list(merged.values())
        projects.sort(key=lambda p: p.relevance_score, reverse=True)
        return projects
    
    def _merge_single_project(self, existing: ProjectBrief, new: ProjectBrief) -> ProjectBrief:
        """Merge two project briefs for the same project."""
        # Use the more recent last_discussed date
        last_discussed = max(existing.last_discussed, new.last_discussed)
        
        # Merge tech stacks (union)
        tech_stack = list(set(existing.tech_stack + new.tech_stack))
        
        # Merge challenges (union)
        key_challenges = list(set(existing.key_challenges + new.key_challenges))
        
        # Use newer description if it's longer/more detailed
        description = (
            new.description 
            if len(new.description) > len(existing.description)
            else existing.description
        )
        
        # Use newer status
        current_status = new.current_status if new.current_status else existing.current_status
        
        # Use higher relevance score
        relevance_score = max(existing.relevance_score, new.relevance_score)
        
        return ProjectBrief(
            name=existing.name,  # Keep original name casing
            description=description,
            tech_stack=tech_stack,
            key_challenges=key_challenges,
            current_status=current_status,
            last_discussed=last_discussed,
            relevance_score=relevance_score
        )
    
    def _merge_preferences(self, existing: UserPreferences, new: UserPreferences) -> UserPreferences:
        """Merge user preferences, preferring newer information."""
        # Merge coding style dictionaries
        coding_style = {**existing.coding_style, **new.coding_style}
        
        # Use newer communication style if available
        communication_style = new.communication_style if new.communication_style else existing.communication_style
        
        # Merge preferred tools (union)
        preferred_tools = list(set(existing.preferred_tools + new.preferred_tools))
        
        # Merge work patterns dictionaries
        work_patterns = {**existing.work_patterns, **new.work_patterns}
        
        return UserPreferences(
            coding_style=coding_style,
            communication_style=communication_style,
            preferred_tools=preferred_tools,
            work_patterns=work_patterns
        )
    
    def _merge_technical_context(self, existing: TechnicalContext, new: TechnicalContext) -> TechnicalContext:
        """Merge technical contexts (union of all lists)."""
        return TechnicalContext(
            languages=list(set(existing.languages + new.languages)),
            frameworks=list(set(existing.frameworks + new.frameworks)),
            tools=list(set(existing.tools + new.tools)),
            domains=list(set(existing.domains + new.domains))
        )
    
    def _version_to_tuple(self, version: str) -> Tuple[int, ...]:
        """Convert version string to tuple for comparison."""
        try:
            # Handle delta versions
            if version.startswith("delta-"):
                # Delta versions sort after regular versions
                return (999, 999, 999)
            
            parts = version.split('.')
            return tuple(int(part) for part in parts)
        except ValueError:
            # If version format is unexpected, put it at the end
            return (999, 999, 999)