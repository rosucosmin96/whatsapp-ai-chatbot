import os
import json
import tiktoken
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from ..openai_client import OpenAIClient
from ..database import db_manager
from ..database.redis_cache import redis_cache
from whatsapp_bot.utils.logging_config import get_logger
from whatsapp_bot.config import get_model_for_task
from .language_service import LanguageDetectionService
from platform import system_alias

logger = get_logger(__name__)

class ConversationSummarizationService:
    """Service for managing conversation context and summarization"""
    
    def __init__(self, prompts_dir: str = None):
        self.client = OpenAIClient(prompts_dir)
        self.language_service = LanguageDetectionService()
        
        # Set prompts directory
        if prompts_dir is None:
            prompts_dir = os.getenv("PROMPTS_DIR", "prompts")
        self.prompts_dir = prompts_dir
        
        # Configuration from environment variables
        self.max_context_tokens = int(os.getenv('MAX_CONTEXT_TOKENS', '3000'))
        self.summary_trigger_tokens = int(os.getenv('SUMMARY_TRIGGER_TOKENS', '2500'))
        self.summary_target_tokens = int(os.getenv('SUMMARY_TARGET_TOKENS', '800'))
        self.keep_recent_messages = int(os.getenv('KEEP_RECENT_MESSAGES', '4'))
        
        # Initialize tokenizer for the current model
        model = get_model_for_task("summarization")
        try:
            if "gpt-4" in model:
                self.encoding = tiktoken.encoding_for_model("gpt-4")
            else:
                self.encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
        except KeyError:
            # Fallback to cl100k_base encoding
            self.encoding = tiktoken.get_encoding("cl100k_base")
        
        self.redis_client = redis_cache.redis_client
        logger.info("Conversation service initialized")
    
    def count_tokens(self, messages: List[Dict[str, str]]) -> int:
        """Count tokens in a list of messages"""
        total_tokens = 0
        
        for message in messages:
            # Count tokens for role and content
            total_tokens += len(self.encoding.encode(message.get("role", "")))
            total_tokens += len(self.encoding.encode(message.get("content", "")))
            # Add overhead tokens per message (OpenAI format overhead)
            total_tokens += 4
        
        # Add overhead for the conversation
        total_tokens += 2
        
        return total_tokens
    
    def count_text_tokens(self, text: str) -> int:
        """Count tokens in a text string"""
        return len(self.encoding.encode(text))
    
    def _load_system_prompt(self, language: str) -> str:
        """Load system prompt from file"""
        prompt_file = os.path.join(self.prompts_dir, f"{language}.txt")
        
        # If language-specific prompt file doesn't exist, fall back to English
        if not os.path.exists(prompt_file):
            prompt_file = os.path.join(self.prompts_dir, "english.txt")
            logger.warning(f"System prompt file for {language} not found, falling back to English")
        
        # Read the system prompt file
        try:
            with open(prompt_file, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception as e:
            logger.error(f"Error reading system prompt file: {str(e)}")
            return "You are a helpful assistant. Answer questions clearly and concisely."
    
    def _load_summary_prompt(self, language: str) -> str:
        """Load summary prompt from file"""
        summary_prompt_file = os.path.join(self.prompts_dir, f"summary_{language}.txt")
        
        # If language-specific summary prompt file doesn't exist, fall back to English
        if not os.path.exists(summary_prompt_file):
            summary_prompt_file = os.path.join(self.prompts_dir, "summary_english.txt")
            logger.warning(f"Summary prompt file for {language} not found, falling back to English")
        
        # Read the summary prompt file
        try:
            with open(summary_prompt_file, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception as e:
            logger.error(f"Error reading summary prompt file: {str(e)}")
            # Fallback summary prompt
            if language == "romanian":
                return """Creează un rezumat detaliat al acestei conversații între utilizator și asistent. 
                Rezumatul trebuie să includă toate subiectele principale, întrebările și răspunsurile, 
                și orice context important pentru continuarea conversației."""
            else:
                return """Create a detailed summary of this conversation between user and assistant. 
                The summary should include all main topics, questions and answers, 
                and any important context for continuing the conversation."""
    
    def create_conversation_summary(self, messages: List[Dict[str, str]], 
                                  language: str = "english") -> str:
        """Create a detailed summary of the conversation"""
        
        # Prepare the conversation text
        conversation_text = ""
        for msg in messages:
            role = "User" if msg["role"] == "user" else "Assistant"
            conversation_text += f"{role}: {msg['content']}\n"
        
        # Load system prompt and summary prompt from files
        system_prompt = self._load_system_prompt(language)
        summary_prompt = self._load_summary_prompt(language)
        
        # Combine system prompt with summary prompt
        combined_system_prompt = f"{system_prompt}\n\n{summary_prompt}"
        
        # Create the user message with conversation text
        user_message = f"Conversation to summarize:\n\n{conversation_text}"
        
        messages_for_summary = [
            {"role": "system", "content": combined_system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        try:
            summary, usage_info = self.client.chat_completion(
                model=get_model_for_task("summarization"),
                messages=messages_for_summary,
                max_tokens=self.summary_target_tokens,
                temperature=0.3
            )
            
            # Log usage information
            logger.info(f"Summary created successfully. Tokens used: {usage_info.get('total_tokens', 'unknown') if usage_info else 'unknown'}")
            
            return summary
            
        except Exception as e:
            logger.error(f"Error creating summary: {str(e)}")
            # Fallback: create a simple summary
            recent_topics = []
            for msg in messages[-3:]:
                if len(msg['content']) > 50:
                    recent_topics.append(msg['content'][:50] + '...')
                else:
                    recent_topics.append(msg['content'])
            
            fallback_summary = f"Previous conversation covered: {', '.join(recent_topics)}"
            return fallback_summary
    
    def get_optimized_conversation_context(self, db: Session, user_id: int, 
                                         current_message: str, receiver_phone: str = None) -> Tuple[List[Dict[str, str]], bool]:
        """
        Get optimized conversation context, with summarization if needed
        
        Args:
            db: Database session
            user_id: User ID
            current_message: Current message from user
            receiver_phone: Optional receiver phone to filter conversation
        
        Returns:
            Tuple[List[Dict[str, str]], bool]: (messages, was_summarized)
        """
        
        # Get full conversation history, filtered by receiver_phone if provided
        conversation_history = db_manager.get_user_conversation_history(db, user_id, receiver_phone, limit=50)
        
        if not conversation_history:
            return [], False
        
        # Add current message for token counting
        current_msg = {"role": "user", "content": current_message}
        all_messages = conversation_history + [current_msg]
        
        # Count tokens
        total_tokens = self.count_tokens(all_messages)
        
        logger.debug(f"Total conversation tokens: {total_tokens}")
        
        # If under the trigger threshold, return as is
        if total_tokens <= self.summary_trigger_tokens:
            return conversation_history, False
        
        logger.info(f"Token limit exceeded ({total_tokens} > {self.summary_trigger_tokens}), creating summary...")
        
        # Determine how many recent messages to keep
        recent_messages = conversation_history[-self.keep_recent_messages:]
        older_messages = conversation_history[:-self.keep_recent_messages]
        
        if not older_messages:
            # If we only have recent messages, just truncate
            return recent_messages, False
        
        # Get user language from recent messages
        language = self._detect_conversation_language(recent_messages)
        
        # Create summary of older messages
        summary = self.create_conversation_summary(older_messages, language)
        
        # Create summary message with proper formatting
        if language == "romanian":
            summary_prefix = "[REZUMAT CONVERSAȚIE]"
        else:
            summary_prefix = "[CONVERSATION SUMMARY]"
            
        summary_message = {
            "role": "system", 
            "content": f"{summary_prefix}: {summary}"
        }
        
        # Combine summary with recent messages
        optimized_context = [summary_message] + recent_messages
        
        # Cache the optimized context 
        try:
            cache_key = f"summary:{user_id}:{datetime.now().strftime('%Y%m%d%H')}"
            self.redis_client.setex(
                cache_key, 
                3600,  # 1 hour TTL
                json.dumps(optimized_context)
            )
            logger.debug(f"Cached optimized context with key: {cache_key}")
        except Exception as e:
            logger.warning(f"Error caching summary: {str(e)}")
        
        new_token_count = self.count_tokens(optimized_context)
        logger.info(f"✅ Summary created successfully!")
        logger.info(f"   Original tokens: {total_tokens}")
        logger.info(f"   Optimized tokens: {new_token_count}")
        logger.info(f"   Token reduction: {total_tokens - new_token_count} ({((total_tokens - new_token_count) / total_tokens * 100):.1f}%)")
        
        return optimized_context, True
    
    def _detect_conversation_language(self, messages: List[Dict[str, str]]) -> str:
        """Detect the primary language of recent conversation"""
        recent_text = " ".join([msg["content"] for msg in messages[-3:] if msg["role"] == "user"])
        
        if not recent_text:
            return self.language_service.get_default_language()
        
        try:
            detected_language = self.language_service.detect_language(recent_text)
            return detected_language
        except:
            return self.language_service.get_default_language()
    
    def get_conversation_stats(self, db: Session, user_id: int) -> Dict:
        """Get conversation statistics for monitoring"""
        conversation_history = db_manager.get_user_conversation_history(db, user_id, limit=100)
        
        if not conversation_history:
            return {"total_messages": 0, "total_tokens": 0, "needs_summary": False}
        
        total_tokens = self.count_tokens(conversation_history)
        
        return {
            "total_messages": len(conversation_history),
            "total_tokens": total_tokens,
            "needs_summary": total_tokens > self.summary_trigger_tokens,
            "max_context_tokens": self.max_context_tokens,
            "summary_trigger_tokens": self.summary_trigger_tokens,
            "token_efficiency": f"{((self.summary_trigger_tokens - total_tokens) / self.summary_trigger_tokens * 100):.1f}%" if total_tokens <= self.summary_trigger_tokens else "Needs optimization"
        }
    
    def force_create_summary(self, db: Session, user_id: int, language: str = None) -> Dict:
        """Force create a summary for testing or manual optimization"""
        conversation_history = db_manager.get_user_conversation_history(db, user_id, limit=50)
        
        if not conversation_history:
            return {"error": "No conversation history found"}
        
        if language is None:
            language = self._detect_conversation_language(conversation_history)
        
        # Create summary
        summary = self.create_conversation_summary(conversation_history, language)
        
        # Calculate token savings
        original_tokens = self.count_tokens(conversation_history)
        summary_tokens = self.count_text_tokens(summary)
        
        return {
            "summary": summary,
            "language": language,
            "original_tokens": original_tokens,
            "summary_tokens": summary_tokens,
            "token_reduction": original_tokens - summary_tokens,
            "efficiency_gain": f"{((original_tokens - summary_tokens) / original_tokens * 100):.1f}%"
        }
