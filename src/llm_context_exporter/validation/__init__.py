"""
Validation and testing components.

This module contains functionality for generating validation tests
and verifying successful context transfer to target platforms.
"""

from .generator import ValidationGenerator

__all__ = [
    "ValidationGenerator",
]