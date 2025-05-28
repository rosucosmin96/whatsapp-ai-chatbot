import os
import json
import redis
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Redis configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
CACHE_TTL = 30 * 60  # 30 minutes in seconds

class RedisCache:
    """Redis cache manager for chat interactions"""
    
    def __init__(self):
        """Initialize Redis connection"""
        self.redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            password=REDIS_PASSWORD,
            decode_responses=True  # Automatically decode responses to strings
        )
        self.ttl = CACHE_TTL
    
    def get_user_key(self, user_id: int) -> str:
        """Generate Redis key for user conversation history"""
        return f"user:{user_id}:conversations"
    
    def cache_interaction(self, user_id: int, role: str, content: str) -> None:
        """
        Cache a single interaction message
        
        Args:
            user_id: User ID
            role: Message role ('user' or 'assistant')
            content: Message content
        """
        key = self.get_user_key(user_id)
        # Serialize the message
        message = json.dumps({"role": role, "content": content})
        # Add to the list with RPUSH (appends to the right/end of the list)
        self.redis_client.rpush(key, message)
        # Reset TTL whenever we add new data
        self.redis_client.expire(key, self.ttl)
    
    def cache_conversation(self, user_id: int, conversation: List[Dict[str, str]]) -> None:
        """
        Cache a full conversation
        
        Args:
            user_id: User ID
            conversation: List of conversation messages
        """
        key = self.get_user_key(user_id)
        # Clear existing data
        self.redis_client.delete(key)
        
        # Add each message to the list
        for message in conversation:
            serialized = json.dumps(message)
            self.redis_client.rpush(key, serialized)
        
        # Set expiration
        self.redis_client.expire(key, self.ttl)
    
    def get_conversation(self, user_id: int) -> Optional[List[Dict[str, str]]]:
        """
        Get cached conversation for a user
        
        Args:
            user_id: User ID
            
        Returns:
            List of conversation messages or None if not in cache
        """
        key = self.get_user_key(user_id)
        # Check if key exists
        if not self.redis_client.exists(key):
            return None
        
        # Get all elements from the list
        serialized_messages = self.redis_client.lrange(key, 0, -1)
        
        # Deserialize each message
        messages = []
        for msg in serialized_messages:
            messages.append(json.loads(msg))
        
        # Reset TTL when accessed
        self.redis_client.expire(key, self.ttl)
        
        return messages
    
    def clear_user_cache(self, user_id: int) -> None:
        """
        Clear cached conversation for a user
        
        Args:
            user_id: User ID
        """
        key = self.get_user_key(user_id)
        self.redis_client.delete(key)
    
    def health_check(self) -> bool:
        """
        Check if Redis connection is healthy
        
        Returns:
            True if connection is healthy, False otherwise
        """
        try:
            return self.redis_client.ping()
        except Exception:
            return False

# Create singleton instance
redis_cache = RedisCache() 