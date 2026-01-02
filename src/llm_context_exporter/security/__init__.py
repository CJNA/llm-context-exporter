"""
Security and privacy components.

This module contains functionality for encryption, sensitive data detection,
secure file handling, network monitoring, and user redaction prompting.
"""

from .encryption import FileEncryption
from .detection import SensitiveDataDetector
from .deletion import SecureFileDeleter
from .network_monitor import NetworkActivityMonitor, NetworkViolationError, LocalOnlyValidator, network_monitor, local_validator
from .redaction import RedactionPrompter, prompt_for_redaction_approval
from .manager import SecurityManager, security_manager

__all__ = [
    "FileEncryption",
    "SensitiveDataDetector", 
    "SecureFileDeleter",
    "NetworkActivityMonitor",
    "NetworkViolationError", 
    "LocalOnlyValidator",
    "network_monitor",
    "local_validator",
    "RedactionPrompter",
    "prompt_for_redaction_approval",
    "SecurityManager",
    "security_manager",
]