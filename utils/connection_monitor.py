#!/usr/bin/env python3
"""
Connection status and error monitoring utilities.
Tracks connection health, timeouts, and errors for external services.
"""

import socket
import time
import logging
import traceback
from contextlib import contextmanager
from typing import Callable, Optional, Any, Dict, Union, Generator
from functools import wraps

# Set up logging
logger = logging.getLogger(__name__)

class ConnectionStatus:
    """Store connection status information and metrics."""
    
    def __init__(self):
        self.connected = False
        self.start_time = None
        self.end_time = None
        self.duration = None
        self.error = None
        self.error_type = None
        self.response_size = None
        self.retry_count = 0
        self.warning = None
    
    def start(self):
        """Mark the start of a connection attempt."""
        self.start_time = time.time()
        self.connected = False
        
    def success(self, response_size: Optional[int] = None):
        """Mark a successful connection."""
        self.connected = True
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        self.response_size = response_size
        
    def failure(self, error: Exception):
        """Mark a failed connection with error details."""
        self.connected = False
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        self.error = str(error)
        self.error_type = type(error).__name__
        
    def warning(self, message: str):
        """Add a warning message to the status."""
        self.warning = message
        
    def format_status(self) -> str:
        """Format a human-readable status message."""
        if not self.start_time:
            return "[CONNECTION STATUS: Not started]"
            
        if not self.end_time:
            elapsed = time.time() - self.start_time
            return f"[CONNECTION STATUS: In progress for {elapsed:.2f}s]"
            
        if self.connected:
            msg = f"[CONNECTION STATUS: Connected, completed in {self.duration:.2f}s"
            if self.response_size:
                msg += f", received {self.response_size} bytes"
            if self.retry_count:
                msg += f", after {self.retry_count} retries"
            msg += "]"
            return msg
        else:
            return f"[CONNECTION ERROR: {self.error_type}: {self.error}, after {self.duration:.2f}s]"
            
    def to_dict(self) -> Dict[str, Any]:
        """Convert status to dictionary for serialization."""
        return {
            "connected": self.connected,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "error": self.error,
            "error_type": self.error_type,
            "response_size": self.response_size,
            "retry_count": self.retry_count,
            "warning": self.warning
        }


@contextmanager
def connection_monitor(
    name: str = "External Service",
    timeout: float = 30.0,
    log_callback: Optional[Callable[[str], Any]] = None,
    retry_count: int = 0
) -> Generator[ConnectionStatus, None, None]:
    """
    Context manager for monitoring connection status and timing.
    
    Args:
        name: Name of the service being connected to
        timeout: Maximum expected time in seconds before warning
        log_callback: Optional function to call with status messages
        retry_count: Number of previous retry attempts
        
    Yields:
        ConnectionStatus object that can be used to track the connection
    
    Example:
        with connection_monitor("LLM Provider", log_callback=agent.log) as status:
            response = llm_provider.generate(prompt)
            status.response_size = len(response)
    """
    status = ConnectionStatus()
    status.retry_count = retry_count
    status.start()
    
    # Helper function to log messages both to logger and callback if provided
    def log_status(message: str, level: str = "info"):
        getattr(logger, level)(message)
        if log_callback:
            log_callback(message)
            
    log_status(f"[CONNECTION STATUS: Connecting to {name}]")
    
    try:
        yield status
        
        # If status wasn't updated in the block, mark as success
        if not status.end_time:
            status.success()
            
        if status.connected:
            if status.duration > timeout:
                warning = f"Request to {name} took {status.duration:.2f}s, exceeding timeout of {timeout}s"
                status.warning = warning
                log_status(f"[CONNECTION WARNING: {warning}]", "warning")
            else:
                log_status(status.format_status())
                
    except (socket.timeout, socket.error, ConnectionError, TimeoutError) as e:
        status.failure(e)
        log_status(f"[CONNECTION ERROR: {status.error_type} when connecting to {name}: {status.error}]", "error")
        
    except Exception as e:
        status.failure(e)
        log_status(f"[ERROR: Unexpected {status.error_type} when connecting to {name}: {status.error}]", "error")
        log_status(f"[TRACEBACK: {traceback.format_exc()}]", "debug")


def monitor_connection(
    name: str = "External Service",
    timeout: float = 30.0,
    max_retries: int = 0,
    retry_delay: float = 1.0,
    log_callback: Optional[Callable[[str], Any]] = None
):
    """
    Decorator for functions that make external connections.
    Tracks status, handles retries, and logs connection events.
    
    Args:
        name: Name of the service being connected to
        timeout: Maximum expected time in seconds before warning
        max_retries: Maximum number of retry attempts (0 = no retries)
        retry_delay: Delay between retries in seconds
        log_callback: Optional function to call with status messages
        
    Returns:
        Decorated function that tracks connection status
        
    Example:
        @monitor_connection("LLM Provider", max_retries=3, log_callback=agent.log)
        def call_llm_api(prompt):
            return llm_client.generate(prompt)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retry = 0
            last_error = None
            
            while retry <= max_retries:
                with connection_monitor(name, timeout, log_callback, retry) as status:
                    if retry > 0:
                        time.sleep(retry_delay)
                        
                    try:
                        result = func(*args, **kwargs)
                        return result
                    except (socket.timeout, socket.error, ConnectionError, TimeoutError) as e:
                        last_error = e
                        retry += 1
                        if retry <= max_retries:
                            continue
                        else:
                            raise
                
            # This point should never be reached as the last retry will either
            # return successfully or raise an exception, but added for safety
            if last_error:
                raise last_error
            return None
            
        return wrapper
    return decorator


async def check_connectivity(url: str = "https://www.google.com", timeout: float = 5.0) -> bool:
    """
    Check if internet connectivity is available.
    
    Args:
        url: URL to check for connectivity
        timeout: Connection timeout in seconds
        
    Returns:
        True if connection successful, False otherwise
    """
    import urllib.request
    
    try:
        urllib.request.urlopen(url, timeout=timeout)
        return True
    except:
        return False


# Example usage for the autonomous agent
if __name__ == "__main__":
    # Configure basic logging
    logging.basicConfig(level=logging.INFO)
    
    def demo_log(message):
        print(f"LOG: {message}")
    
    # Example with context manager
    print("\nExample 1: Context Manager with successful connection")
    with connection_monitor("Demo Service", log_callback=demo_log) as status:
        # Simulate API call
        time.sleep(0.5)
        status.response_size = 1024
        
    # Example with context manager and error
    print("\nExample 2: Context Manager with connection error")
    try:
        with connection_monitor("Demo Service", log_callback=demo_log):
            # Simulate connection error
            time.sleep(0.5)
            raise ConnectionError("Could not connect to server")
    except ConnectionError:
        pass
        
    # Example with decorator
    print("\nExample 3: Decorator with retries")
    
    @monitor_connection("API Service", max_retries=2, log_callback=demo_log)
    def api_call(succeed_after=0):
        global attempt
        if attempt < succeed_after:
            attempt += 1
            raise ConnectionError(f"Simulated connection failure (attempt {attempt})")
        return "API response data"
        
    attempt = 0
    result = api_call(succeed_after=1)
    print(f"Result: {result}") 