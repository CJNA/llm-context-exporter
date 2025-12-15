"""
Network activity monitoring utilities.

This module provides monitoring to ensure all processing happens locally
without any network requests being made.
"""

import socket
import threading
import time
from typing import List, Dict, Any, Optional, Callable
from contextlib import contextmanager
import warnings


class NetworkActivityMonitor:
    """
    Monitors network activity to ensure local-only processing.
    
    Tracks socket creation and network requests to verify that
    no data leaves the user's machine during processing.
    """
    
    def __init__(self):
        """Initialize the network monitor."""
        self._original_socket = socket.socket
        self._original_getaddrinfo = socket.getaddrinfo
        self._monitoring = False
        self._network_calls = []
        self._lock = threading.Lock()
        self._violation_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    
    def set_violation_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """
        Set callback function to be called when network activity is detected.
        
        Args:
            callback: Function to call with violation details
        """
        self._violation_callback = callback
    
    def start_monitoring(self):
        """Start monitoring network activity."""
        if self._monitoring:
            return
        
        self._monitoring = True
        self._network_calls.clear()
        
        # Monkey patch socket creation
        def monitored_socket(*args, **kwargs):
            call_info = {
                'type': 'socket_creation',
                'args': args,
                'kwargs': kwargs,
                'timestamp': time.time(),
                'thread': threading.current_thread().name
            }
            
            with self._lock:
                self._network_calls.append(call_info)
            
            if self._violation_callback:
                self._violation_callback(call_info)
            
            # Still create the socket but log the violation
            return self._original_socket(*args, **kwargs)
        
        # Monkey patch DNS resolution
        def monitored_getaddrinfo(*args, **kwargs):
            call_info = {
                'type': 'dns_resolution',
                'args': args,
                'kwargs': kwargs,
                'timestamp': time.time(),
                'thread': threading.current_thread().name
            }
            
            with self._lock:
                self._network_calls.append(call_info)
            
            if self._violation_callback:
                self._violation_callback(call_info)
            
            # Still perform DNS resolution but log the violation
            return self._original_getaddrinfo(*args, **kwargs)
        
        socket.socket = monitored_socket
        socket.getaddrinfo = monitored_getaddrinfo
    
    def stop_monitoring(self):
        """Stop monitoring network activity."""
        if not self._monitoring:
            return
        
        self._monitoring = False
        
        # Restore original functions
        socket.socket = self._original_socket
        socket.getaddrinfo = self._original_getaddrinfo
    
    def get_network_calls(self) -> List[Dict[str, Any]]:
        """
        Get list of detected network calls.
        
        Returns:
            List of network call information
        """
        with self._lock:
            return self._network_calls.copy()
    
    def has_network_activity(self) -> bool:
        """
        Check if any network activity was detected.
        
        Returns:
            True if network calls were detected
        """
        with self._lock:
            return len(self._network_calls) > 0
    
    def clear_calls(self):
        """Clear the recorded network calls."""
        with self._lock:
            self._network_calls.clear()
    
    @contextmanager
    def monitor_context(self, strict: bool = True):
        """
        Context manager for monitoring network activity.
        
        Args:
            strict: If True, raises exception on network activity
            
        Yields:
            The monitor instance
            
        Raises:
            NetworkViolationError: If network activity detected and strict=True
        """
        self.start_monitoring()
        try:
            yield self
        finally:
            self.stop_monitoring()
            
            if strict and self.has_network_activity():
                calls = self.get_network_calls()
                raise NetworkViolationError(
                    f"Network activity detected during local-only processing: {len(calls)} calls made",
                    calls
                )


class NetworkViolationError(Exception):
    """Exception raised when network activity is detected during local-only processing."""
    
    def __init__(self, message: str, network_calls: List[Dict[str, Any]]):
        """
        Initialize the exception.
        
        Args:
            message: Error message
            network_calls: List of detected network calls
        """
        super().__init__(message)
        self.network_calls = network_calls


class LocalOnlyValidator:
    """
    Validates that operations are performed locally only.
    
    Provides decorators and context managers to ensure functions
    don't make any network requests.
    """
    
    def __init__(self):
        """Initialize the validator."""
        self.monitor = NetworkActivityMonitor()
    
    def local_only(self, func):
        """
        Decorator to ensure a function performs only local operations.
        
        Args:
            func: Function to wrap
            
        Returns:
            Wrapped function that monitors network activity
        """
        def wrapper(*args, **kwargs):
            with self.monitor.monitor_context(strict=True):
                return func(*args, **kwargs)
        
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    
    def warn_on_network(self, func):
        """
        Decorator to warn if a function makes network requests.
        
        Args:
            func: Function to wrap
            
        Returns:
            Wrapped function that warns on network activity
        """
        def wrapper(*args, **kwargs):
            with self.monitor.monitor_context(strict=False):
                result = func(*args, **kwargs)
                
                if self.monitor.has_network_activity():
                    calls = self.monitor.get_network_calls()
                    warnings.warn(
                        f"Function {func.__name__} made {len(calls)} network calls. "
                        "This may violate local-only processing requirements.",
                        UserWarning
                    )
                
                return result
        
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper


# Global instance for easy access
network_monitor = NetworkActivityMonitor()
local_validator = LocalOnlyValidator()