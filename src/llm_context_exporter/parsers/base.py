"""
Base interface for platform-specific parsers.

This module defines the abstract base class that all platform parsers must implement.
"""

from abc import ABC, abstractmethod
from typing import Optional
from ..core.models import ParsedExport


class UnsupportedFormatError(Exception):
    """Raised when the export format version is not supported."""
    pass


class ParseError(Exception):
    """Raised when the export file is corrupted or invalid."""
    pass


class PlatformParser(ABC):
    """
    Abstract base class for platform-specific export parsers.
    
    Each platform (ChatGPT, Claude, etc.) should implement this interface
    to handle their specific export formats.
    """
    
    @abstractmethod
    def parse_export(self, file_path: str) -> ParsedExport:
        """
        Parse platform export file into normalized conversation format.
        
        Args:
            file_path: Path to the export file
            
        Returns:
            ParsedExport containing conversations with metadata
            
        Raises:
            UnsupportedFormatError: If format version is not supported
            ParseError: If file is corrupted or invalid
            FileNotFoundError: If file doesn't exist
        """
        pass
    
    @abstractmethod
    def detect_format_version(self, file_path: str) -> str:
        """
        Detect the export format version.
        
        Args:
            file_path: Path to the export file
            
        Returns:
            Format version string (e.g., "2023-04-01", "v1.0")
            
        Raises:
            ParseError: If version cannot be determined
        """
        pass
    
    @abstractmethod
    def get_supported_versions(self) -> list[str]:
        """
        Get list of supported format versions.
        
        Returns:
            List of supported version strings
        """
        pass
    
    def validate_file(self, file_path: str) -> bool:
        """
        Validate that the file can be parsed by this parser.
        
        Args:
            file_path: Path to the export file
            
        Returns:
            True if file appears to be valid for this parser
        """
        try:
            self.detect_format_version(file_path)
            return True
        except (ParseError, UnsupportedFormatError):
            return False
    
    def get_parser_info(self) -> dict:
        """
        Get information about this parser.
        
        Returns:
            Dictionary with parser metadata (name, supported_platforms, etc.)
        """
        return {
            "name": self.__class__.__name__,
            "supported_versions": self.get_supported_versions(),
            "description": self.__doc__ or "No description available"
        }