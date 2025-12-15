"""
Platform-specific formatters for generating output.

This module contains formatters that convert UniversalContextPack data
into formats optimized for specific target LLM platforms.
"""

from .base import PlatformFormatter
from .gemini import GeminiFormatter
from .ollama import OllamaFormatter

__all__ = [
    "PlatformFormatter",
    "GeminiFormatter", 
    "OllamaFormatter",
]