"""
Configuration module for the Chainlit UI application

This module handles loading and managing configuration from environment variables.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration class for the Chainlit UI application"""
    
    # API Configuration
    API_BASE_URL: str = os.getenv("API_BASE_URL", "http://localhost:8000")
    
    # User Configuration  
    DEFAULT_PHONE: str = os.getenv("DEFAULT_PHONE", "+1234567890")
    
    # Chainlit Server Configuration
    CHAINLIT_HOST: str = os.getenv("CHAINLIT_HOST", "0.0.0.0")
    CHAINLIT_PORT: int = int(os.getenv("CHAINLIT_PORT", "8080"))
    
    # Request Configuration
    REQUEST_TIMEOUT: float = float(os.getenv("REQUEST_TIMEOUT", "60.0"))
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()
    
    # Feature Flags
    ENABLE_HISTORY: bool = os.getenv("ENABLE_HISTORY", "true").lower() == "true"
    ENABLE_STATUS_CHECKS: bool = os.getenv("ENABLE_STATUS_CHECKS", "true").lower() == "true"
    
    @classmethod
    def get_api_url(cls) -> str:
        """Get the properly formatted API base URL"""
        return cls.API_BASE_URL.rstrip('/')
    
    @classmethod
    def validate(cls) -> bool:
        """Validate the configuration"""
        required_vars = ["API_BASE_URL", "DEFAULT_PHONE"]
        
        for var in required_vars:
            if not getattr(cls, var):
                print(f"❌ Missing required configuration: {var}")
                return False
        
        return True
    
    @classmethod
    def print_config(cls):
        """Print current configuration (for debugging)"""
        print("🔧 Current Configuration:")
        print(f"  API_BASE_URL: {cls.API_BASE_URL}")
        print(f"  DEFAULT_PHONE: {cls.DEFAULT_PHONE}")
        print(f"  CHAINLIT_HOST: {cls.CHAINLIT_HOST}")
        print(f"  CHAINLIT_PORT: {cls.CHAINLIT_PORT}")
        print(f"  REQUEST_TIMEOUT: {cls.REQUEST_TIMEOUT}s")
        print(f"  LOG_LEVEL: {cls.LOG_LEVEL}")
        print(f"  ENABLE_HISTORY: {cls.ENABLE_HISTORY}")
        print(f"  ENABLE_STATUS_CHECKS: {cls.ENABLE_STATUS_CHECKS}")


# Global config instance
config = Config() 