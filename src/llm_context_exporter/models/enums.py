"""
Enums for LLM Context Exporter.

Common enumeration types used throughout the application.
"""

from enum import Enum


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