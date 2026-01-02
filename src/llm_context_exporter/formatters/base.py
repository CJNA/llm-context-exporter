"""
Base interface for platform-specific formatters.

This module defines the abstract base class that all platform formatters must implement.
"""

from abc import ABC, abstractmethod
from typing import Union
from ..core.models import UniversalContextPack, GeminiOutput, OllamaOutput


class FormattingError(Exception):
    """Raised when formatting fails."""
    pass


class SizeLimitExceededError(FormattingError):
    """Raised when the formatted output exceeds platform limits."""
    pass


class PlatformFormatter(ABC):
    """
    Abstract base class for platform-specific output formatters.
    
    Each target platform (Gemini, Ollama, etc.) should implement this interface
    to convert UniversalContextPack data into platform-optimized formats.
    """
    
    @abstractmethod
    def format_context(self, context: UniversalContextPack) -> Union[GeminiOutput, OllamaOutput]:
        """
        Format context pack for the target platform.
        
        Args:
            context: Universal context pack to format
            
        Returns:
            Platform-specific output object
            
        Raises:
            FormattingError: If formatting fails
            SizeLimitExceededError: If output exceeds platform limits
        """
        pass
    
    @abstractmethod
    def get_size_limits(self) -> dict:
        """
        Get size limits for this platform.
        
        Returns:
            Dictionary with size limits (e.g., {"max_text_length": 32000})
        """
        pass
    
    @abstractmethod
    def check_size_constraints(self, context: UniversalContextPack) -> dict:
        """
        Check if context fits within platform size constraints.
        
        Args:
            context: Context pack to check
            
        Returns:
            Dictionary with size check results:
            {
                "fits": bool,
                "current_size": int,
                "max_size": int,
                "suggestions": List[str]  # If doesn't fit
            }
        """
        pass
    
    @abstractmethod
    def prioritize_content(self, context: UniversalContextPack, max_size: int) -> UniversalContextPack:
        """
        Trim context to fit size constraints while preserving most important info.
        
        Args:
            context: Original context pack
            max_size: Maximum allowed size
            
        Returns:
            Trimmed context pack that fits within size limits
        """
        pass
    
    def get_formatter_info(self) -> dict:
        """
        Get information about this formatter.
        
        Returns:
            Dictionary with formatter metadata
        """
        return {
            "name": self.__class__.__name__,
            "target_platform": getattr(self, 'target_platform', 'unknown'),
            "size_limits": self.get_size_limits(),
            "description": self.__doc__ or "No description available"
        }
    
    def validate_context(self, context: UniversalContextPack) -> list[str]:
        """
        Validate context pack for formatting.
        
        Args:
            context: Context pack to validate
            
        Returns:
            List of validation warnings (empty if valid)
        """
        warnings = []
        
        if not context.projects:
            warnings.append("No projects found in context")
        
        if not context.user_profile.expertise_areas:
            warnings.append("No expertise areas identified")
        
        if not context.technical_context.languages:
            warnings.append("No programming languages identified")
        
        return warnings