"""
Platform-specific parsers for extracting conversation data.

This module contains parsers for different LLM platforms' export formats.
Currently supports ChatGPT exports.
"""

from .base import PlatformParser
from .chatgpt import ChatGPTParser

__all__ = [
    "PlatformParser",
    "ChatGPTParser",
]