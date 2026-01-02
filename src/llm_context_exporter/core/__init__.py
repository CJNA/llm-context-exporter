"""
Core functionality for the LLM Context Exporter.

This module contains the core data models, extraction engine, and filtering logic
that are platform-agnostic.
"""

from .models import (
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

from ..models.payment import (
    PaymentIntent,
    BetaUser,
    UsageStats,
    Feedback,
)

from .extractor import ContextExtractor
from .filter import FilterEngine
from .payment import PaymentManager

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
    "PaymentIntent",
    "BetaUser",
    "UsageStats",
    "Feedback",
    "ContextExtractor",
    "FilterEngine",
    "PaymentManager",
]