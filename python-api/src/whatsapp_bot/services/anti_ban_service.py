import asyncio
import random
import time
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from sqlalchemy.orm import Session
from ..database import db_manager
from ..database.redis_cache import redis_cache
from ..utils.logging_config import get_logger

logger = get_logger(__name__)

class AntiBanService:
    """Service for implementing anti-ban measures to prevent WhatsApp account suspension"""
    
    def __init__(self, config_manager=None):
        self.config_manager = config_manager
        
        # If config manager is provided, use config; otherwise fall back to environment variables
        if config_manager:
            anti_ban_config = config_manager.get_anti_ban_config()
            self.max_new_users_per_hour = anti_ban_config.max_new_users_per_hour
            self.min_reply_delay = anti_ban_config.min_reply_delay
            self.max_reply_delay = anti_ban_config.max_reply_delay
            self.global_message_rate_limit = anti_ban_config.global_rate_limit
            self.daily_message_limits = anti_ban_config.daily_message_limits
        else:
            # Fallback to environment variables for backward compatibility
            self.max_new_users_per_hour = int(os.getenv('MAX_NEW_USERS_PER_HOUR', '10'))
            self.min_reply_delay = float(os.getenv('MIN_REPLY_DELAY', '2.0'))
            self.max_reply_delay = float(os.getenv('MAX_REPLY_DELAY', '5.0'))
            self.global_message_rate_limit = float(os.getenv('GLOBAL_RATE_LIMIT', '1.0'))
            # Default warm-up configuration
            self.daily_message_limits = {
                1: 20,   # Week 1: 20 messages/day
                2: 50,   # Week 2: 50 messages/day  
                3: 100,  # Week 3: 100 messages/day
                4: 200   # Week 4+: 200 messages/day
            }
        
        # Spam detection patterns
        self.spam_patterns = [
            'buy now', 'limited offer', 'click this link', 'urgent', 'act now',
            'free money', 'guaranteed', 'no risk', 'limited time', 'exclusive deal'
        ]
        
        self.redis_client = redis_cache.redis_client
        logger.info("Anti-ban service initialized")
    
    def _is_anti_ban_enabled(self) -> bool:
        """Check if anti-ban measures are enabled"""
        if self.config_manager:
            return getattr(self.config_manager.get_anti_ban_config(), 'enabled', True)
        return True  # Default to enabled if no config manager
    
    async def should_allow_message(self, user_phone: str, db: Session) -> Tuple[bool, Optional[str]]:
        """
        Check if we should allow processing this message based on anti-ban rules
        
        Returns:
            Tuple[bool, Optional[str]]: (allow_message, reason_if_blocked)
        """
        
        # If anti-ban is disabled, always allow
        if not self._is_anti_ban_enabled():
            return True, None
        
        # Check if user is opted out
        if await self._is_user_opted_out(user_phone):
            return False, "User has opted out"
        
        # Check global rate limiting
        if not await self._check_global_rate_limit():
            return False, "Global rate limit exceeded"
        
        # Check new user rate limiting
        user = db_manager.get_user_by_phone(db, user_phone)
        if not user:
            if not await self._check_new_user_rate_limit():
                return False, "New user rate limit exceeded"
        
        # Check daily message limits (warm-up)
        if not await self._check_daily_message_limit():
            return False, "Daily message limit exceeded"
        
        return True, None
    
    async def get_human_like_delay(self) -> float:
        """Generate a human-like delay before responding"""
        # If anti-ban is disabled, return minimal delay
        if not self._is_anti_ban_enabled():
            return 0.1  # Minimal delay for system processing
        
        base_delay = random.uniform(self.min_reply_delay, self.max_reply_delay)
        
        # Add some variation based on time of day (slower at night)
        current_hour = datetime.now().hour
        if 22 <= current_hour or current_hour <= 6:  # Night time
            base_delay *= 1.5
        
        return base_delay
    
    async def check_message_for_spam(self, message: str) -> Tuple[bool, Optional[str]]:
        """
        Check if message contains spam-like content
        
        Returns:
            Tuple[bool, Optional[str]]: (is_spam, detected_pattern)
        """
        # If anti-ban is disabled, don't check for spam
        if not self._is_anti_ban_enabled():
            return False, None
        
        message_lower = message.lower()
        
        for pattern in self.spam_patterns:
            if pattern in message_lower:
                return True, pattern
        
        # Check for excessive links
        link_count = message_lower.count('http://') + message_lower.count('https://')
        if link_count > 2:
            return True, "excessive_links"
        
        # Check for excessive caps
        if len(message) > 10 and sum(1 for c in message if c.isupper()) / len(message) > 0.7:
            return True, "excessive_caps"
        
        return False, None
    
    async def sanitize_response(self, response: str) -> str:
        """
        Sanitize AI response to make it more human-like and less spammy
        """
        # If anti-ban is disabled, return response as-is
        if not self._is_anti_ban_enabled():
            return response
        
        # Remove or replace promotional language
        response = response.replace("Buy now", "Consider purchasing")
        response = response.replace("Click here", "You can check")
        response = response.replace("Limited time", "For a while")
        
        # Add some human-like imperfections occasionally
        if random.random() < 0.1:  # 10% chance
            response = self._add_human_imperfection(response)
        
        return response
    
    async def record_message_sent(self, user_phone: str):
        """Record that a message was sent for rate limiting purposes"""
        # If anti-ban is disabled, don't record for rate limiting
        if not self._is_anti_ban_enabled():
            return
        
        try:
            # Update global rate limiting
            self.redis_client.setex("last_message_sent", 3600, str(time.time()))
            
            # Update daily message count
            today = datetime.now().strftime("%Y-%m-%d")
            daily_key = f"daily_messages:{today}"
            self.redis_client.incr(daily_key)
            self.redis_client.expire(daily_key, 86400)  # 24 hours
            
            # Update new user tracking if applicable
            new_user_key = f"new_user_messages:{datetime.now().strftime('%Y-%m-%d-%H')}"
            user_exists_key = f"user_exists:{user_phone}"
            
            if not self.redis_client.exists(user_exists_key):
                self.redis_client.incr(new_user_key)
                self.redis_client.expire(new_user_key, 3600)  # 1 hour
                self.redis_client.setex(user_exists_key, 86400 * 7, "1")  # Mark as existing for 7 days
            
        except Exception as e:
            logger.warning(f"Error recording message sent: {str(e)}")
    
    async def handle_opt_out(self, user_phone: str, message: str) -> bool:
        """
        Check if user wants to opt out and handle it
        
        Returns:
            bool: True if user opted out
        """
        # Always handle opt-out regardless of anti-ban settings
        opt_out_keywords = ['stop', 'unsubscribe', 'opt out', 'quit', 'leave me alone']
        message_lower = message.lower().strip()
        
        if any(keyword in message_lower for keyword in opt_out_keywords):
            await self._set_user_opted_out(user_phone)
            logger.info(f"User {user_phone} opted out")
            return True
        
        return False
    
    async def _check_global_rate_limit(self) -> bool:
        """Check if we're within global rate limits"""
        try:
            last_message = self.redis_client.get("last_message_sent")
            if last_message:
                time_since_last = time.time() - float(last_message)
                if time_since_last < self.global_message_rate_limit:
                    return False
            return True
        except Exception as e:
            logger.warning(f"Error checking global rate limit: {str(e)}")
            return True  # Allow on error
    
    async def _check_new_user_rate_limit(self) -> bool:
        """Check if we're within new user rate limits"""
        try:
            current_hour = datetime.now().strftime("%Y-%m-%d-%H")
            new_user_key = f"new_user_messages:{current_hour}"
            current_count = self.redis_client.get(new_user_key) or 0
            return int(current_count) < self.max_new_users_per_hour
        except Exception as e:
            logger.warning(f"Error checking new user rate limit: {str(e)}")
            return True  # Allow on error
    
    async def _check_daily_message_limit(self) -> bool:
        """Check daily message limits for warm-up period"""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            daily_key = f"daily_messages:{today}"
            current_count = int(self.redis_client.get(daily_key) or 0)
            
            # Determine which week we're in (simplified - could be more sophisticated)
            week_number = min(4, max(1, (datetime.now().day // 7) + 1))
            daily_limit = self.daily_message_limits[week_number]
            
            return current_count < daily_limit
        except Exception as e:
            logger.warning(f"Error checking daily message limit: {str(e)}")
            return True  # Allow on error
    
    async def _is_user_opted_out(self, user_phone: str) -> bool:
        """Check if user has opted out"""
        try:
            opt_out_key = f"opted_out:{user_phone}"
            return bool(self.redis_client.exists(opt_out_key))
        except Exception as e:
            logger.warning(f"Error checking opt-out status: {str(e)}")
            return False
    
    async def _set_user_opted_out(self, user_phone: str):
        """Mark user as opted out"""
        try:
            opt_out_key = f"opted_out:{user_phone}"
            self.redis_client.setex(opt_out_key, 86400 * 365, "1")  # 1 year
        except Exception as e:
            logger.error(f"Error setting opt-out status: {str(e)}")
    
    def _add_human_imperfection(self, response: str) -> str:
        """Add subtle human-like imperfections to responses"""
        imperfections = [
            lambda s: s.replace(".", ".."),  # Double periods
            lambda s: s.replace("I am", "I'm"),  # Contractions
            lambda s: s.replace("you are", "you're"),
            lambda s: s.replace("cannot", "can't"),
        ]
        
        # Apply random imperfection
        if imperfections:
            imperfection = random.choice(imperfections)
            return imperfection(response)
        
        return response
    
    async def get_conversation_stats(self) -> Dict:
        """Get anti-ban related statistics"""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            current_hour = datetime.now().strftime("%Y-%m-%d-%H")
            
            daily_count = int(self.redis_client.get(f"daily_messages:{today}") or 0)
            hourly_new_users = int(self.redis_client.get(f"new_user_messages:{current_hour}") or 0)
            
            week_number = min(4, max(1, (datetime.now().day // 7) + 1))
            daily_limit = self.daily_message_limits[week_number]
            
            return {
                "daily_messages_sent": daily_count,
                "daily_limit": daily_limit,
                "daily_remaining": max(0, daily_limit - daily_count),
                "new_users_this_hour": hourly_new_users,
                "new_user_limit": self.max_new_users_per_hour,
                "week_number": week_number,
                "rate_limit_status": "healthy" if daily_count < daily_limit * 0.8 else "approaching_limit"
            }
        except Exception as e:
            logger.error(f"Error getting conversation stats: {str(e)}")
            return {"error": "Unable to retrieve stats"} 