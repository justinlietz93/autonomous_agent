"""Test configuration that doesn't require dotenv"""
import os

class Config:
    """Minimal config for testing"""
    def __init__(self):
        pass

class Settings:
    """Minimal settings for testing"""
    LLM_PROVIDER = "test"
    MODEL_NAME = "test"
    MAX_TOKENS = 1000

settings = Settings() 