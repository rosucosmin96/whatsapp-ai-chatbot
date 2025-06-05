"""
Chatbot API Client for WhatsApp OpenAI Bot

This module handles communication with the Python API backend.
"""

import httpx
import asyncio
from typing import Dict, Any, Optional
import os
from dotenv import load_dotenv
import logging
from dataclasses import dataclass

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PromptResponse:
    """Response structure for prompt retrieval by language"""
    language: str
    system_prompt: str
    summary_prompt: Optional[str]
    has_summary_prompt: bool
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PromptResponse':
        """Create PromptResponse from dictionary"""
        return cls(
            language=data["language"],
            system_prompt=data["system_prompt"],
            summary_prompt=data.get("summary_prompt"),
            has_summary_prompt=data["has_summary_prompt"]
        )


class ChatbotAPIClient:
    """Client for communicating with the WhatsApp OpenAI Bot Python API"""
    
    def __init__(self, base_url: str, timeout: float = 60.0):
        """
        Initialize the API client
        
        Args:
            base_url: Base URL of the Python API
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
        logger.info(f"ChatbotAPIClient initialized with base_url: {self.base_url}")
    
    async def send_message(self, phone: str, message: str) -> Dict[str, Any]:
        """
        Send a message to the chatbot API
        
        Args:
            phone: Phone number for the user session
            message: Message content to send
            
        Returns:
            Dict containing the API response
            
        Raises:
            Exception: If the API request fails
        """
        url = f"{self.base_url}/chat"
        payload = {
            "phone": phone,
            "message": message
        }
        
        try:
            logger.info(f"Sending message to API: {phone} -> {message[:50]}...")
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Received response from API: {result.get('response', '')[:50]}...")
            return result
            
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
            logger.error(f"API request failed with status error: {error_msg}")
            raise Exception(f"API request failed: {error_msg}")
        except httpx.RequestError as e:
            error_msg = f"Request error: {str(e)}"
            logger.error(f"API request failed with request error: {error_msg}")
            raise Exception(f"Failed to connect to API: {error_msg}")
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"API request failed with unexpected error: {error_msg}")
            raise Exception(f"API request failed: {error_msg}")
    
    async def get_health_status(self) -> Dict[str, Any]:
        """
        Get the health status of the API
        
        Returns:
            Dict containing health status information
        """
        try:
            url = f"{self.base_url}/health"
            logger.info("Checking API health status")
            response = await self.client.get(url)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"API health status: {result.get('status', 'unknown')}")
            return result
            
        except Exception as e:
            logger.warning(f"Health check failed: {str(e)}")
            return {"status": "unavailable", "error": str(e)}
    
    async def get_redis_health(self) -> Dict[str, Any]:
        """
        Get the Redis health status
        
        Returns:
            Dict containing Redis health information
        """
        try:
            url = f"{self.base_url}/health/redis"
            response = await self.client.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.warning(f"Redis health check failed: {str(e)}")
            return {"status": "unavailable", "error": str(e)}
    
    async def get_anti_ban_health(self) -> Dict[str, Any]:
        """
        Get the anti-ban system health status
        
        Returns:
            Dict containing anti-ban health information
        """
        try:
            url = f"{self.base_url}/health/anti-ban"
            response = await self.client.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.warning(f"Anti-ban health check failed: {str(e)}")
            return {"status": "unavailable", "error": str(e)}
    
    async def get_user_history(self, phone: str, limit: int = 10) -> Dict[str, Any]:
        """
        Get conversation history for a user
        
        Args:
            phone: Phone number of the user
            limit: Maximum number of interactions to return
            
        Returns:
            Dict containing user's conversation history
        """
        try:
            url = f"{self.base_url}/history/{phone}"
            params = {"limit": limit}
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.warning(f"Failed to get user history: {str(e)}")
            return {"error": str(e), "history": []}
    
    async def get_api_info(self) -> Dict[str, Any]:
        """
        Get general API information
        
        Returns:
            Dict containing API information and endpoints
        """
        try:
            url = f"{self.base_url}/"
            response = await self.client.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.warning(f"Failed to get API info: {str(e)}")
            return {"error": str(e)}
    
    async def get_prompts_by_language(self, language: str) -> PromptResponse:
        """
        Get system and summary prompts for a specific language
        
        Args:
            language: Language code to get prompts for (e.g., "english", "romanian", "default")
            
        Returns:
            PromptResponse containing system prompt, summary prompt, and language information
        """
        try:
            url = f"{self.base_url}/config/prompts/{language}"
            logger.info(f"Getting prompts for language: {language}")
            response = await self.client.get(url)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Retrieved prompts for language '{language}' - has_summary: {result.get('has_summary_prompt', False)}")
            return PromptResponse.from_dict(result)
            
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
            logger.error(f"Failed to get prompts for language '{language}': {error_msg}")
            raise Exception(f"Failed to get prompts for language '{language}': {error_msg}")
        except httpx.RequestError as e:
            error_msg = f"Request error: {str(e)}"
            logger.error(f"Failed to get prompts for language '{language}': {error_msg}")
            raise Exception(f"Failed to connect to API: {error_msg}")
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"Failed to get prompts for language '{language}': {error_msg}")
            raise Exception(f"Failed to get prompts: {error_msg}")
    
    async def update_prompts_by_language(self, language: str, system_prompt: Optional[str] = None, summary_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Update system and/or summary prompts for a specific language
        
        Args:
            language: Language code to update prompts for (e.g., "english", "romanian", "default")
            system_prompt: New system prompt text (optional)
            summary_prompt: New summary prompt text (optional)
            
        Returns:
            Dict containing update status and information
        """
        if system_prompt is None and summary_prompt is None:
            raise ValueError("At least one of system_prompt or summary_prompt must be provided")
        
        try:
            url = f"{self.base_url}/config/prompt/{language}"
            payload = {}
            
            if system_prompt is not None:
                payload["system_prompt"] = system_prompt
            if summary_prompt is not None:
                payload["summary_prompt"] = summary_prompt
            
            logger.info(f"Updating prompts for language '{language}' - system: {system_prompt is not None}, summary: {summary_prompt is not None}")
            response = await self.client.put(url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Successfully updated prompts for language '{language}' - files: {result.get('updated_files', [])}")
            return result
            
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
            logger.error(f"Failed to update prompts for language '{language}': {error_msg}")
            raise Exception(f"Failed to update prompts for language '{language}': {error_msg}")
        except httpx.RequestError as e:
            error_msg = f"Request error: {str(e)}"
            logger.error(f"Failed to update prompts for language '{language}': {error_msg}")
            raise Exception(f"Failed to connect to API: {error_msg}")
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"Failed to update prompts for language '{language}': {error_msg}")
            raise Exception(f"Failed to update prompts: {error_msg}")
        
    async def erase_user_data(self, phone: str) -> Dict[str, Any]:
        """
        Erase all user data for a specific phone number
        
        Args:
            phone: Phone number of the user to erase data for
            
        Returns:
            Dict containing erase status and details
        """
        try:
            url = f"{self.base_url}/config/erase/{phone}"
            response = await self.client.delete(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
            logger.error(f"Failed to erase user data for phone '{phone}': {error_msg}")
            raise Exception(f"Failed to erase user data: {error_msg}")
        except httpx.RequestError as e:
            error_msg = f"Request error: {str(e)}"
            logger.error(f"Failed to erase user data for phone '{phone}': {error_msg}")
            raise Exception(f"Failed to connect to API: {error_msg}")
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"Failed to erase user data for phone '{phone}': {error_msg}")
            raise Exception(f"Failed to erase user data: {error_msg}")
    
    async def close(self):
        """Close the HTTP client connection"""
        await self.client.aclose()
        logger.info("ChatbotAPIClient connection closed")
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()


def create_api_client(base_url: Optional[str] = None, timeout: float = 60.0) -> ChatbotAPIClient:
    """
    Factory function to create a ChatbotAPIClient instance
    
    Args:
        base_url: Base URL of the API (defaults to environment variable)
        timeout: Request timeout in seconds
        
    Returns:
        ChatbotAPIClient instance
    """
    if base_url is None:
        base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
    
    return ChatbotAPIClient(base_url, timeout) 