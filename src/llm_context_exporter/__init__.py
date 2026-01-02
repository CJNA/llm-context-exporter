"""
LLM Context Exporter - A tool for migrating context between LLM platforms.

This package enables users to export their conversation history from ChatGPT
and package it for use with other LLM platforms like Gemini or local models via Ollama.
"""

__version__ = "0.1.0"
__author__ = "LLM Context Exporter Team"

from .core.models import (
    ParsedExport,
    Conversation,
    Message,
    UniversalContextPack,
    UserProfile,
    ProjectBrief,
    UserPreferences,
    TechnicalContext,
    GeminiOutput,
    OllamaOutput,
    ValidationSuite,
    ValidationQuestion,
    FilterConfig,
    ExportConfig,
)

from .parsers.base import PlatformParser
from .formatters.base import PlatformFormatter
from .core.payment import PaymentManager

__all__ = [
    "ParsedExport",
    "Conversation", 
    "Message",
    "UniversalContextPack",
    "UserProfile",
    "ProjectBrief",
    "UserPreferences",
    "TechnicalContext",
    "GeminiOutput",
    "OllamaOutput",
    "ValidationSuite",
    "ValidationQuestion",
    "FilterConfig",
    "ExportConfig",
    "PlatformParser",
    "PlatformFormatter",
    "PaymentManager",
]