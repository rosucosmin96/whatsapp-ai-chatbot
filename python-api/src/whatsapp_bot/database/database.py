import os
import json
import redis
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv
from typing import List, Optional, Dict, Any
from whatsapp_bot.utils.logging_config import get_logger

from .models import Base, User, ChatInteraction, UsageLog
from .schema import ChatInteraction as ChatInteractionModel
from .redis_cache import redis_cache

logger = get_logger(__name__)

# Load environment variables
load_dotenv()

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://chatbot_user:securepass@localhost/chatbot")
engine = create_engine(DATABASE_URL)

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Redis setup
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = None
try:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    redis_client.ping()  # Test connection
    logger.info("Redis connection established")
except Exception as e:
    logger.warning(f"Redis connection failed: {str(e)}")
    redis_client = None

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
        raise

class DatabaseManager:
    def __init__(self):
        self.SessionLocal = SessionLocal
    
    def get_session(self):
        """Get a new database session"""
        return self.SessionLocal()
    
    # User operations
    def get_user_by_phone(self, db: Session, phone: str) -> Optional[User]:
        """Get a user by phone number"""
        return db.query(User).filter(User.phone == phone).first()
    
    def create_user(self, db: Session, phone: str) -> User:
        """Create a new user"""
        user = User(phone=phone)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    def get_or_create_user(self, db: Session, phone: str) -> User:
        """Get a user by phone or create if not exists"""
        user = self.get_user_by_phone(db, phone)
        if not user:
            user = self.create_user(db, phone)
        return user
    
    # ChatInteraction operations
    def save_chat_interaction(self, db: Session, 
                             user_id: int,
                             request_message: str,
                             response_message: str,
                             language: str) -> ChatInteraction:
        """Save a chat interaction to the database"""
        interaction = ChatInteraction(
            user_id=user_id,
            request_message=request_message,
            response_message=response_message,
            language=language
        )
        db.add(interaction)
        db.commit()
        db.refresh(interaction)
        
        # Cache the interaction in Redis
        try:
            redis_cache.cache_interaction(user_id, "user", request_message)
            redis_cache.cache_interaction(user_id, "assistant", response_message)
        except Exception as e:
            logger.warning(f"Redis caching error: {str(e)}")
        
        return interaction
    
    def save_interaction(self, db: Session, 
                        interaction: ChatInteractionModel) -> ChatInteraction:
        """Save a chat interaction from request and response models"""
        user = self.get_user_by_phone(db, interaction.chat_request.phone)
        return self.save_chat_interaction(
            db=db,
            user_id=user.id,
            request_message=interaction.chat_request.message,
            response_message=interaction.chat_response.response,
            language=interaction.language
        )
    
    def get_user_conversation_history(self, db: Session, user_id: int, limit: int = 10) -> List[Dict[str, str]]:
        """Get recent conversation history for a user in format suitable for OpenAI"""
        # Try to get conversation from Redis cache first
        try:
            cached_conversation = redis_cache.get_conversation(user_id)
            if cached_conversation:
                logger.debug(f"Using cached conversation for user {user_id}")
                return cached_conversation
        except Exception as e:
            logger.warning(f"Redis cache retrieval error: {str(e)}")
        
        # If not in cache or error occurred, fall back to database
        logger.debug(f"Cache miss for user {user_id}, retrieving from database")
        interactions = db.query(ChatInteraction).filter(
            ChatInteraction.user_id == user_id
        ).order_by(ChatInteraction.created_at).limit(limit).all()
        
        # Convert to list of dictionaries for OpenAI and reverse for chronological order
        conversation = []
        for interaction in reversed(interactions):
            conversation.append({"role": "user", "content": interaction.request_message})
            conversation.append({"role": "assistant", "content": interaction.response_message})
        
        # Cache the conversation for future use
        try:
            redis_cache.cache_conversation(user_id, conversation)
        except Exception as e:
            logger.warning(f"Redis caching error: {str(e)}")
        
        return conversation
    
    def get_user_interactions(self, db: Session, user_id: int, limit: int = 10) -> List[ChatInteraction]:
        """Get all interactions for a user"""
        return db.query(ChatInteraction).filter(
            ChatInteraction.user_id == user_id
        ).order_by(ChatInteraction.created_at).limit(limit).all()
    
    # Token usage tracking
    def log_token_usage(self, db: Session, 
                       interaction_id: int, 
                       model: str,
                       prompt_tokens: int, 
                       completion_tokens: int) -> UsageLog:
        """Log token usage for cost tracking"""
        total_tokens = prompt_tokens + completion_tokens
        
        # Calculate approximate cost in microdollars (actual cost * 1,000,000)
        if model.startswith("gpt-4"):
            prompt_cost = int(prompt_tokens * 0.03 * 1_000_000 / 1000)
            completion_cost = int(completion_tokens * 0.06 * 1_000_000 / 1000)
        else:  # gpt-3.5-turbo
            prompt_cost = int(prompt_tokens * 0.0005 * 1_000_000 / 1000)
            completion_cost = int(completion_tokens * 0.0015 * 1_000_000 / 1000)
        
        estimated_cost = prompt_cost + completion_cost
        
        usage_log = UsageLog(
            interaction_id=interaction_id,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost=estimated_cost
        )
        
        db.add(usage_log)
        db.commit()
        db.refresh(usage_log)
        return usage_log

# Create a singleton instance
db_manager = DatabaseManager() 

def get_redis_client():
    """Get Redis client"""
    return redis_client

def save_message(user_phone: str, role: str, content: str, language: str = 'english'):
    """Save a message to the database"""
    try:
        db = SessionLocal()
        message = Message(
            user_phone=user_phone,
            role=role,
            content=content,
            language=language
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        db.close()
        
        # Cache invalidation
        if redis_client:
            try:
                cache_key = f"conversation:{user_phone}"
                redis_client.delete(cache_key)
                logger.debug(f"Invalidated cache for user {user_phone}")
            except Exception as e:
                logger.warning(f"Redis caching error: {str(e)}")
        
        logger.debug(f"Message saved for user {user_phone}")
        return message
        
    except Exception as e:
        logger.error(f"Error saving message: {str(e)}")
        raise

def get_conversation_history(user_phone: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Get conversation history for a user"""
    try:
        # Try to get from cache first
        if redis_client:
            try:
                cache_key = f"conversation:{user_phone}"
                cached_data = redis_client.get(cache_key)
                if cached_data:
                    logger.debug(f"Using cached conversation for user {user_phone}")
                    return json.loads(cached_data)
            except Exception as e:
                logger.warning(f"Redis cache retrieval error: {str(e)}")
        
        logger.debug(f"Cache miss for user {user_phone}, retrieving from database")
        
        # Get from database
        db = SessionLocal()
        messages = db.query(Message).filter(
            Message.user_phone == user_phone
        ).order_by(Message.timestamp.desc()).limit(limit).all()
        
        # Convert to list of dicts
        history = []
        for message in reversed(messages):  # Reverse to get chronological order
            history.append({
                'role': message.role,
                'content': message.content,
                'language': message.language,
                'timestamp': message.timestamp.isoformat()
            })
        
        db.close()
        
        # Cache the result
        if redis_client and history:
            try:
                cache_key = f"conversation:{user_phone}"
                redis_client.setex(cache_key, 3600, json.dumps(history))  # Cache for 1 hour
                logger.debug(f"Cached conversation for user {user_phone}")
            except Exception as e:
                logger.warning(f"Redis caching error: {str(e)}")
        
        return history
        
    except Exception as e:
        logger.error(f"Error retrieving conversation history: {str(e)}")
        return []

def get_user_stats(user_phone: str) -> Dict[str, Any]:
    """Get statistics for a user"""
    try:
        db = SessionLocal()
        
        total_messages = db.query(Message).filter(
            Message.user_phone == user_phone
        ).count()
        
        user_messages = db.query(Message).filter(
            Message.user_phone == user_phone,
            Message.role == 'user'
        ).count()
        
        assistant_messages = db.query(Message).filter(
            Message.user_phone == user_phone,
            Message.role == 'assistant'
        ).count()
        
        # Get first and last message timestamps
        first_message = db.query(Message).filter(
            Message.user_phone == user_phone
        ).order_by(Message.timestamp.asc()).first()
        
        last_message = db.query(Message).filter(
            Message.user_phone == user_phone
        ).order_by(Message.timestamp.desc()).first()
        
        db.close()
        
        stats = {
            'total_messages': total_messages,
            'user_messages': user_messages,
            'assistant_messages': assistant_messages,
            'first_message': first_message.timestamp.isoformat() if first_message else None,
            'last_message': last_message.timestamp.isoformat() if last_message else None
        }
        
        logger.debug(f"Retrieved stats for user {user_phone}")
        return stats
        
    except Exception as e:
        logger.error(f"Error retrieving user stats: {str(e)}")
        return {}

def clear_conversation_history(user_phone: str) -> bool:
    """Clear conversation history for a user"""
    try:
        db = SessionLocal()
        
        # Delete messages
        deleted_count = db.query(Message).filter(
            Message.user_phone == user_phone
        ).delete()
        
        db.commit()
        db.close()
        
        # Clear cache
        if redis_client:
            try:
                cache_key = f"conversation:{user_phone}"
                redis_client.delete(cache_key)
            except Exception as e:
                logger.warning(f"Error clearing cache: {str(e)}")
        
        logger.info(f"Cleared {deleted_count} messages for user {user_phone}")
        return True
        
    except Exception as e:
        logger.error(f"Error clearing conversation history: {str(e)}")
        return False 