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
    """Configuration for API providers."""
    
    # API Keys
    DEEPSEEK_API_KEY: str = os.getenv('DEEPSEEK_API_KEY')
    ANTHROPIC_API_KEY: str = os.getenv('ANTHROPIC_API_KEY')
    
    # Model settings
    DEEPSEEK_MAX_TOKENS: int = 64000  # Context window
    DEEPSEEK_OUTPUT_MAX: int = 8192   # Max output tokens
    
    # Claude settings
    CLAUDE_MODEL: str = os.getenv('CLAUDE_MODEL', 'claude-3-5-sonnet-20241022')
    
    # Temperature recommendations
    TEMPERATURE_SETTINGS = {
        "coding": 0.0,
        "data_analysis": 1.0,
        "conversation": 1.3,
        "translation": 1.3,
        "creative": 1.5
    }
    
    @classmethod
    def validate(cls) -> None:
        """Validate required configuration."""
        if not cls.DEEPSEEK_API_KEY:
            raise ValueError(
                "Missing DEEPSEEK_API_KEY environment variable. "
                "Please add it to your .env file."
            )
        if not cls.ANTHROPIC_API_KEY:
            raise ValueError(
                "Missing ANTHROPIC_API_KEY environment variable. "
                "Please add it to your .env file."
            )

# Validate config on import
Config.validate()

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