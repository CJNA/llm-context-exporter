"""
Sensitive data detection utilities.

This module provides pattern matching for detecting potentially sensitive information.
"""

import re
from typing import List, Dict, Any


class SensitiveDataDetector:
    """
    Detects potentially sensitive information in text content.
    
    Uses regex patterns to identify emails, API keys, phone numbers,
    and other personally identifiable information.
    """
    
    def __init__(self):
        """Initialize the detector with common patterns."""
        self._setup_patterns()
    
    def _setup_patterns(self):
        """Set up regex patterns for sensitive data detection."""
        self.patterns = {
            'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'phone': re.compile(r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b'),
            'api_key': re.compile(r'\b(?:sk-|pk_|rk_|xoxb-|xoxp-|ghp_|gho_|ghu_|ghs_|ghr_)[A-Za-z0-9_-]{20,}\b'),  # Common API key prefixes
            'generic_key': re.compile(r'\b[A-Za-z0-9]{32,}\b'),  # Generic long alphanumeric strings
            'credit_card': re.compile(r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3[0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b'),
            'ssn': re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
            'ip_address': re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'),
            'aws_access_key': re.compile(r'\bAKIA[0-9A-Z]{16}\b'),
            'aws_secret_key': re.compile(r'\b[A-Za-z0-9/+=]{40}\b'),
            'jwt_token': re.compile(r'\beyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*\b'),
            'password_field': re.compile(r'(?i)(?:password|passwd|pwd)\s*[:=]\s*["\']?([^"\'\s]+)["\']?'),
            'private_key': re.compile(r'-----BEGIN (?:RSA )?PRIVATE KEY-----'),
            'url_with_auth': re.compile(r'https?://[^:\s]+:[^@\s]+@[^\s]+'),
            'home_directory': re.compile(r'\b/Users/[^/\s]+\b|\bC:\\Users\\[^\\s]+\b'),
            'file_path': re.compile(r'\b(?:[A-Za-z]:\\|/)[^\s<>"|*?]+\b'),
        }
    
    def detect_sensitive_data(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect sensitive data in the given text.
        
        Args:
            text: Text content to analyze
            
        Returns:
            List of detected sensitive data items with type and location
        """
        detections = []
        
        for data_type, pattern in self.patterns.items():
            matches = pattern.finditer(text)
            for match in matches:
                detections.append({
                    'type': data_type,
                    'value': match.group(),
                    'start': match.start(),
                    'end': match.end(),
                    'context': self._get_context(text, match.start(), match.end())
                })
        
        return detections
    
    def has_sensitive_data(self, text: str) -> bool:
        """
        Check if text contains any sensitive data.
        
        Args:
            text: Text content to check
            
        Returns:
            True if sensitive data is detected
        """
        return len(self.detect_sensitive_data(text)) > 0
    
    def redact_sensitive_data(self, text: str, replacement: str = "[REDACTED]") -> str:
        """
        Redact sensitive data from text.
        
        Args:
            text: Text content to redact
            replacement: Replacement string for sensitive data
            
        Returns:
            Text with sensitive data redacted
        """
        redacted_text = text
        
        # Apply redaction patterns in reverse order to maintain positions
        detections = self.detect_sensitive_data(text)
        detections.sort(key=lambda x: x['start'], reverse=True)
        
        for detection in detections:
            start, end = detection['start'], detection['end']
            redacted_text = redacted_text[:start] + replacement + redacted_text[end:]
        
        return redacted_text
    
    def _get_context(self, text: str, start: int, end: int, context_length: int = 50) -> str:
        """Get surrounding context for a detected item."""
        context_start = max(0, start - context_length)
        context_end = min(len(text), end + context_length)
        
        context = text[context_start:context_end]
        
        # Mark the sensitive part
        relative_start = start - context_start
        relative_end = end - context_start
        
        return (
            context[:relative_start] + 
            ">>>" + context[relative_start:relative_end] + "<<<" + 
            context[relative_end:]
        )