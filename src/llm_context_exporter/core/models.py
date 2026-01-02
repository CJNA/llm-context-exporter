"""
Core data models for the LLM Context Exporter.

This module defines all the data structures used throughout the application,
including input parsing models, the Universal Context Pack, and output models.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum


# Input Models (from parsing)

@dataclass
class Message:
    """Individual message in a conversation."""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Conversation:
    """Single conversation thread."""
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[Message]


@dataclass
class ParsedExport:
    """Raw parsed data from ChatGPT export."""
    format_version: str
    export_date: datetime
    conversations: List[Conversation]
    metadata: Dict[str, Any] = field(default_factory=dict)


# Universal Context Pack Models

@dataclass
class UserProfile:
    """User background and role."""
    role: Optional[str] = None  # e.g., "Software Engineer", "Data Scientist"
    expertise_areas: List[str] = field(default_factory=list)  # e.g., ["Python", "Machine Learning"]
    background_summary: str = ""


@dataclass
class ProjectBrief:
    """Summary of a specific project."""
    name: str
    description: str
    tech_stack: List[str] = field(default_factory=list)
    key_challenges: List[str] = field(default_factory=list)
    current_status: str = ""
    last_discussed: datetime = field(default_factory=datetime.now)
    relevance_score: float = 0.0  # For prioritization


@dataclass
class UserPreferences:
    """User working patterns and preferences."""
    coding_style: Dict[str, str] = field(default_factory=dict)  # e.g., {"language": "Python", "style": "functional"}
    communication_style: str = ""
    preferred_tools: List[str] = field(default_factory=list)
    work_patterns: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TechnicalContext:
    """Technical knowledge and expertise."""
    languages: List[str] = field(default_factory=list)
    frameworks: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    domains: List[str] = field(default_factory=list)  # e.g., ["web development", "data science"]


@dataclass
class UniversalContextPack:
    """Platform-agnostic context representation."""
    version: str  # Schema version
    created_at: datetime
    source_platform: str  # 'chatgpt'
    user_profile: UserProfile
    projects: List[ProjectBrief]
    preferences: UserPreferences
    technical_context: TechnicalContext
    metadata: Dict[str, Any] = field(default_factory=dict)


# Output Models

@dataclass
class ValidationQuestion:
    """Single validation question."""
    question: str
    expected_answer_summary: str
    category: str  # 'project', 'preference', 'technical'


@dataclass
class ValidationSuite:
    """Test questions for validation."""
    questions: List[ValidationQuestion]
    target_platform: str


@dataclass
class GeminiOutput:
    """Formatted output for Gemini."""
    formatted_text: str  # Ready to paste into Gemini Saved Info
    instructions: str  # Step-by-step guide
    validation_tests: ValidationSuite
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OllamaOutput:
    """Formatted output for Ollama."""
    modelfile_content: str  # Complete Modelfile
    supplementary_files: Dict[str, str] = field(default_factory=dict)  # Additional context files if needed
    setup_commands: List[str] = field(default_factory=list)  # Shell commands to create model
    test_commands: List[str] = field(default_factory=list)  # Commands to test the model
    validation_tests: ValidationSuite = field(default_factory=lambda: ValidationSuite([], "ollama"))


# Configuration Models

@dataclass
class FilterConfig:
    """User filtering preferences."""
    excluded_conversation_ids: List[str] = field(default_factory=list)
    excluded_topics: List[str] = field(default_factory=list)
    date_range: Optional[Tuple[datetime, datetime]] = None
    min_relevance_score: float = 0.0


@dataclass
class ExportConfig:
    """Configuration for export operation."""
    input_path: str
    target_platform: str  # 'gemini' or 'ollama'
    output_path: str
    base_model: Optional[str] = None  # For Ollama
    filters: Optional[FilterConfig] = None
    interactive: bool = False
    incremental: bool = False
    previous_context_path: Optional[str] = None


# Enums for better type safety

class TargetPlatform(Enum):
    """Supported target platforms."""
    GEMINI = "gemini"
    OLLAMA = "ollama"


class MessageRole(Enum):
    """Message roles in conversations."""
    USER = "user"
    ASSISTANT = "assistant"


class ValidationCategory(Enum):
    """Categories for validation questions."""
    PROJECT = "project"
    PREFERENCE = "preference"
    TECHNICAL = "technical"