"""
Configuration module for loading environment variables and settings.

This module handles:
1. Loading API keys from .env file
2. Setting default configurations
3. Validating required settings
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration manager for tool settings and API keys."""
    
    # Required API Keys
    DEEPSEEK_API_KEY: str = os.getenv('DEEPSEEK_API_KEY', '')
    
    # Optional API Keys
    ANTHROPIC_API_KEY: str = os.getenv('ANTHROPIC_API_KEY', '')
    GOOGLE_SEARCH_API_KEY: str = os.getenv('GOOGLE_SEARCH_API_KEY', '')
    GOOGLE_SEARCH_ENGINE_ID: str = os.getenv('GOOGLE_SEARCH_ENGINE_ID', '')
    BING_SEARCH_API_KEY: str = os.getenv('BING_SEARCH_API_KEY', '')
    SERP_API_KEY: str = os.getenv('SERP_API_KEY', '')
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")  # or "official_api"
    
    # Optional configurations with defaults
    WEB_BROWSER_TIMEOUT: int = int(os.getenv('WEB_BROWSER_TIMEOUT', '30'))
    DEFAULT_SEARCH_RESULTS: int = int(os.getenv('DEFAULT_SEARCH_RESULTS', '10'))
    
    # Package manager settings
    PACKAGE_MANAGER_CONFIG = {
        "use_module_pip": True,  # Default to python -m pip for better venv support
        "pip_command": None,     # Custom pip command if needed
    }
    
    # Token limits
    DEEPSEEK_MAX_TOKENS = 128000  # DeepSeek's context window
    DEEPSEEK_CHUNK_SIZE = 1000    # Recommended chunk size
    DEEPSEEK_OUTPUT_MAX = 8192    # Max output tokens
    
    def __init__(self):
        """Initialize configuration."""
        if not self.DEEPSEEK_API_KEY:
            raise ValueError("DEEPSEEK_API_KEY environment variable must be set")
    
    
    @classmethod
    def get_api_key(cls, key_name: str) -> Optional[str]:
        """
        Get an API key by name.
        
        Args:
            key_name: Name of the API key to retrieve
            
        Returns:
            The API key value or None if not found
        """
        return getattr(cls, key_name, None)

class Settings:
    # LLM Provider settings
    LLM_PROVIDER = "ollama"
    OLLAMA_HOST = "http://localhost:11434"
    
    # Model settings
    MODEL_NAME = "deepseek-coder"
    MAX_TOKENS = 8000
    
    # Web browser settings
    WEB_BROWSER_TIMEOUT = 30

settings = Settings() 