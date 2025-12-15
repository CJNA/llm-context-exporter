"""
Core data models for LLM Context Exporter.

These models represent the fundamental data structures used throughout
the application for parsing, extracting, and organizing user context.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict


class Message(BaseModel):
    """Individual message in a conversation."""
    
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(..., description="When the message was sent")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional message metadata")
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        if v not in ['user', 'assistant']:
            raise ValueError("Role must be 'user' or 'assistant'")
        return v
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        if not v.strip():
            raise ValueError("Message content cannot be empty")
        return v


class Conversation(BaseModel):
    """Single conversation thread."""
    
    id: str = Field(..., description="Unique conversation identifier")
    title: str = Field(..., description="Conversation title")
    created_at: datetime = Field(..., description="When the conversation was created")
    updated_at: datetime = Field(..., description="When the conversation was last updated")
    messages: List[Message] = Field(default_factory=list, description="Messages in the conversation")
    
    @field_validator('id')
    @classmethod
    def validate_id(cls, v):
        if not v.strip():
            raise ValueError("Conversation ID cannot be empty")
        return v
    
    @field_validator('messages')
    @classmethod
    def validate_messages(cls, v):
        if not v:
            raise ValueError("Conversation must have at least one message")
        return v


class ParsedExport(BaseModel):
    """Raw parsed data from ChatGPT export."""
    
    format_version: str = Field(..., description="Export format version")
    export_date: datetime = Field(..., description="When the export was created")
    conversations: List[Conversation] = Field(default_factory=list, description="Parsed conversations")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional export metadata")
    
    @field_validator('format_version')
    @classmethod
    def validate_format_version(cls, v):
        if not v.strip():
            raise ValueError("Format version cannot be empty")
        return v
    
    @field_validator('conversations')
    @classmethod
    def validate_conversations(cls, v):
        if not v:
            raise ValueError("Export must contain at least one conversation")
        return v


class UserProfile(BaseModel):
    """User background and role information."""
    
    role: Optional[str] = Field(None, description="User's professional role")
    expertise_areas: List[str] = Field(default_factory=list, description="Areas of expertise")
    background_summary: str = Field(default="", description="Summary of user's background")
    
    @field_validator('expertise_areas')
    @classmethod
    def validate_expertise_areas(cls, v):
        # Remove empty strings and duplicates
        return list(set(area.strip() for area in v if area.strip()))


class ProjectBrief(BaseModel):
    """Summary of a specific project."""
    
    name: str = Field(..., description="Project name")
    description: str = Field(..., description="Project description")
    tech_stack: List[str] = Field(default_factory=list, description="Technologies used")
    key_challenges: List[str] = Field(default_factory=list, description="Main challenges faced")
    current_status: str = Field(default="", description="Current project status")
    last_discussed: datetime = Field(..., description="When project was last discussed")
    relevance_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Relevance score for prioritization")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError("Project name cannot be empty")
        return v.strip()
    
    @field_validator('tech_stack')
    @classmethod
    def validate_tech_stack(cls, v):
        # Remove empty strings and duplicates
        return list(set(tech.strip() for tech in v if tech.strip()))
    
    @field_validator('key_challenges')
    @classmethod
    def validate_key_challenges(cls, v):
        # Remove empty strings
        return [challenge.strip() for challenge in v if challenge.strip()]


class UserPreferences(BaseModel):
    """User working patterns and preferences."""
    
    coding_style: Dict[str, str] = Field(default_factory=dict, description="Coding style preferences")
    communication_style: str = Field(default="", description="Preferred communication style")
    preferred_tools: List[str] = Field(default_factory=list, description="Preferred development tools")
    work_patterns: Dict[str, Any] = Field(default_factory=dict, description="Working patterns and habits")
    
    @field_validator('preferred_tools')
    @classmethod
    def validate_preferred_tools(cls, v):
        # Remove empty strings and duplicates
        return list(set(tool.strip() for tool in v if tool.strip()))


class TechnicalContext(BaseModel):
    """Technical knowledge and expertise."""
    
    languages: List[str] = Field(default_factory=list, description="Programming languages")
    frameworks: List[str] = Field(default_factory=list, description="Frameworks and libraries")
    tools: List[str] = Field(default_factory=list, description="Development tools")
    domains: List[str] = Field(default_factory=list, description="Technical domains")
    
    @field_validator('languages')
    @classmethod
    def validate_languages(cls, v):
        # Remove empty strings and duplicates, preserve case for display
        return list(set(lang.strip() for lang in v if lang.strip()))
    
    @field_validator('frameworks')
    @classmethod
    def validate_frameworks(cls, v):
        # Remove empty strings and duplicates
        return list(set(fw.strip() for fw in v if fw.strip()))
    
    @field_validator('tools')
    @classmethod
    def validate_tools(cls, v):
        # Remove empty strings and duplicates
        return list(set(tool.strip() for tool in v if tool.strip()))
    
    @field_validator('domains')
    @classmethod
    def validate_domains(cls, v):
        # Remove empty strings and duplicates, preserve case for display
        return list(set(domain.strip() for domain in v if domain.strip()))


class UniversalContextPack(BaseModel):
    """Platform-agnostic context representation."""
    
    version: str = Field(..., description="Schema version")
    created_at: datetime = Field(default_factory=datetime.now, description="When the context pack was created")
    source_platform: str = Field(..., description="Source platform (e.g., 'chatgpt')")
    user_profile: UserProfile = Field(default_factory=UserProfile, description="User background and role")
    projects: List[ProjectBrief] = Field(default_factory=list, description="User projects")
    preferences: UserPreferences = Field(default_factory=UserPreferences, description="User preferences")
    technical_context: TechnicalContext = Field(default_factory=TechnicalContext, description="Technical knowledge")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @field_validator('version')
    @classmethod
    def validate_version(cls, v):
        if not v.strip():
            raise ValueError("Version cannot be empty")
        return v.strip()
    
    @field_validator('source_platform')
    @classmethod
    def validate_source_platform(cls, v):
        if not v.strip():
            raise ValueError("Source platform cannot be empty")
        return v.strip().lower()
    
    model_config = ConfigDict(
        # Use Pydantic v2 serialization approach
        json_schema_extra={
            "examples": [
                {
                    "version": "1.0",
                    "created_at": "2023-12-14T10:30:00Z",
                    "source_platform": "chatgpt",
                    "user_profile": {},
                    "projects": [],
                    "preferences": {},
                    "technical_context": {},
                    "metadata": {}
                }
            ]
        }
    )