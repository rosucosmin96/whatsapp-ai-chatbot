from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime
import asyncio
from typing import List

from ..openai_client import OpenAIClient
from ..database.schema import ChatRequest, ChatResponse, ChatInteraction as ChatInteractionModel
from ..database import get_db, db_manager, redis_cache
from ..mapper import map_db_interaction_to_api_interaction
from ..services.conversation_service import ConversationSummarizationService
from ..services.anti_ban_service import AntiBanService
from ..config import config_manager
from ..utils.logging_config import get_logger

logger = get_logger(__name__)

class ChatController:
    """Controller for handling chat-related operations"""
    
    def __init__(self, prompts_dir: str):
        self.prompts_dir = prompts_dir
        self.config_manager = config_manager
        self.openai_client = OpenAIClient(prompts_dir)
        self.conversation_service = ConversationSummarizationService(prompts_dir)
        self.anti_ban_service = AntiBanService(self.config_manager)
        logger.info("Chat controller initialized with configuration management")
    
    async def chat_endpoint(self, request: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
        """
        Handle chat interactions with configuration-based access control
        
        Args:
            request: Chat request containing phone and message
            db: Database session
            
        Returns:
            ChatResponse: Response from the AI assistant
        """
        try:
            user_phone = request.phone
            user_message = request.message
            
            logger.info(f"Received message from {user_phone}: {user_message}")
            
            # 1. Check if bot is enabled
            if not self.config_manager.config.enabled:
                return ChatResponse(response="Bot is currently disabled.")
            
            # 2. Check maintenance mode
            if self.config_manager.config.maintenance_mode:
                return ChatResponse(response=self.config_manager.config.maintenance_message)
            
            # 3. Check if number is allowed
            if not self.config_manager.is_number_allowed(user_phone):
                logger.warning(f"Access denied for {user_phone}")
                return ChatResponse(response="")  # Silent rejection
            
            # 4. Handle admin commands
            if self.config_manager.is_admin(user_phone):
                admin_response = await self._handle_admin_commands(user_message)
                if admin_response:
                    return ChatResponse(response=admin_response)
            
            # 5. Check if user wants to opt out
            if await self.anti_ban_service.handle_opt_out(user_phone, user_message):
                return ChatResponse(response="You have been unsubscribed. Send any message to re-enable.")
            
            # 6. Check anti-ban rules
            allow_message, reason = await self.anti_ban_service.should_allow_message(user_phone, db)
            if not allow_message:
                logger.warning(f"Message blocked for {user_phone}: {reason}")
                return ChatResponse(response="")
            
            # 7. Check for spam in user message
            is_spam, spam_reason = await self.anti_ban_service.check_message_for_spam(user_message)
            if is_spam:
                logger.warning(f"Spam detected from {user_phone}: {spam_reason}")
                return ChatResponse(response="I can help you with questions, but please avoid promotional content.")
            
            # 8. Add human-like delay BEFORE processing
            delay = await self.anti_ban_service.get_human_like_delay()
            logger.debug(f"Adding {delay:.2f}s delay before responding to {user_phone}")
            await asyncio.sleep(delay)
            
            # 9. Process message normally
            user = db_manager.get_or_create_user(db, user_phone)
            
            # Get optimized conversation context with summarization
            conversation_history, was_summarized = self.conversation_service.get_optimized_conversation_context(
                db, user.id, user_message
            )
            
            if was_summarized:
                logger.info(f"Used summarized conversation context for {user_phone}")
            
            # Detect language
            language = self.openai_client.detect_language(user_message)
            
            # 10. Get response configuration
            response_config = self.config_manager.get_response_config()
            
            # 11. Generate response with configured settings
            response_message = self.openai_client.generate_response(
                user_message=user_message,
                language=language,
                conversation_history=conversation_history,
                temperature=response_config.temperature,
                max_tokens=response_config.max_tokens,
                response_style=response_config.response_style
            )
            
            # 12. Sanitize response to avoid spam-like content
            response_message = await self.anti_ban_service.sanitize_response(response_message)
            
            logger.info(f"OpenAI response generated successfully")
            logger.debug(f"Response: {response_message}")
            
            # 13. Save interaction
            chat_response = ChatResponse(response=response_message)
            db_manager.save_interaction(
                db=db,
                interaction=ChatInteractionModel(
                    chat_request=request,
                    chat_response=chat_response,
                    timestamp=datetime.now(),
                    language=language
                )
            )
            
            # 14. Record message sent for rate limiting
            await self.anti_ban_service.record_message_sent(user_phone)
            
            logger.info(f"Response sent to {user_phone}")
            return chat_response
            
        except Exception as e:
            logger.error(f"Error in chat endpoint: {str(e)}")
            # Return a human-like error message
            return ChatResponse(response="Sorry, I'm having trouble right now. Could you try again in a moment? 😅")
    
    async def _handle_admin_commands(self, message: str) -> str:
        """Handle admin commands for bot configuration"""
        message_lower = message.lower().strip()
        
        if message_lower.startswith('/config'):
            parts = message_lower.split()
            
            if len(parts) == 1:
                # Show current config
                summary = self.config_manager.get_config_summary()
                return f"📊 Bot Configuration:\n" + "\n".join([f"• {k}: {v}" for k, v in summary.items()])
            
            elif parts[1] == 'reload':
                self.config_manager.reload_config()
                return "✅ Configuration reloaded from file"
            
            elif parts[1] == 'enable':
                self.config_manager.config.enabled = True
                self.config_manager.save_config()
                return "✅ Bot enabled"
            
            elif parts[1] == 'disable':
                self.config_manager.config.enabled = False
                self.config_manager.save_config()
                return "❌ Bot disabled"
            
            elif parts[1] == 'maintenance':
                if len(parts) > 2 and parts[2] == 'on':
                    self.config_manager.set_maintenance_mode(True)
                    return "🔧 Maintenance mode enabled"
                elif len(parts) > 2 and parts[2] == 'off':
                    self.config_manager.set_maintenance_mode(False)
                    return "✅ Maintenance mode disabled"
            
            elif parts[1] == 'whitelist':
                if len(parts) > 2 and parts[2] == 'on':
                    self.config_manager.update_access_config(whitelist_mode=True)
                    return "🔒 Whitelist mode enabled - only allowed numbers can chat"
                elif len(parts) > 2 and parts[2] == 'off':
                    self.config_manager.update_access_config(whitelist_mode=False)
                    return "🔓 Whitelist mode disabled - all numbers can chat (except blocked)"
            
            elif parts[1] == 'tokens' and len(parts) > 2:
                try:
                    max_tokens = int(parts[2])
                    self.config_manager.update_response_config(max_tokens=max_tokens)
                    return f"📝 Response length set to {max_tokens} tokens"
                except ValueError:
                    return "❌ Invalid token count. Use: /config tokens 500"
            
            elif parts[1] == 'style' and len(parts) > 2:
                style = parts[2]
                if style in ['conversational', 'brief', 'detailed']:
                    self.config_manager.update_response_config(response_style=style)
                    return f"🎨 Response style set to {style}"
                else:
                    return "❌ Invalid style. Options: conversational, brief, detailed"
            
            elif parts[1] == 'model' and len(parts) > 3:
                task = parts[2]
                model = parts[3]
                valid_tasks = ['default', 'chat', 'summarization', 'translation', 'analysis', 'creative', 'admin_commands']
                if task in valid_tasks:
                    self.config_manager.update_model_config(**{task: model})
                    return f"🤖 Model for {task} set to {model}"
                else:
                    return f"❌ Invalid task. Options: {', '.join(valid_tasks)}"
            
            elif parts[1] == 'antiban':
                if len(parts) > 2 and parts[2] == 'on':
                    self.config_manager.config.anti_ban.enabled = True
                    self.config_manager.save_config()
                    return "🛡️ Anti-ban measures enabled"
                elif len(parts) > 2 and parts[2] == 'off':
                    self.config_manager.config.anti_ban.enabled = False
                    self.config_manager.save_config()
                    return "🔓 Anti-ban measures disabled"
                else:
                    status = "enabled" if self.config_manager.config.anti_ban.enabled else "disabled"
                    return f"🛡️ Anti-ban measures are currently {status}"
        
        elif message_lower.startswith('/allow'):
            parts = message.split()
            if len(parts) > 1:
                phone = parts[1]
                self.config_manager.add_allowed_number(phone)
                return f"✅ Added {phone} to allowed numbers"
            return "❌ Usage: /allow +1234567890"
        
        elif message_lower.startswith('/block'):
            parts = message.split()
            if len(parts) > 1:
                phone = parts[1]
                self.config_manager.add_blocked_number(phone)
                return f"🚫 Added {phone} to blocked numbers"
            return "❌ Usage: /block +1234567890"
        
        elif message_lower.startswith('/unblock'):
            parts = message.split()
            if len(parts) > 1:
                phone = parts[1]
                self.config_manager.remove_blocked_number(phone)
                return f"✅ Removed {phone} from blocked numbers"
            return "❌ Usage: /unblock +1234567890"
        
        elif message_lower.startswith('/admin'):
            parts = message.split()
            if len(parts) > 1:
                phone = parts[1]
                self.config_manager.add_admin_number(phone)
                return f"👑 Added {phone} to admin numbers"
            return "❌ Usage: /admin +1234567890"
        
        elif message_lower.startswith('/unadmin'):
            parts = message.split()
            if len(parts) > 1:
                phone = parts[1]
                self.config_manager.remove_admin_number(phone)
                return f"👤 Removed {phone} from admin numbers"
            return "❌ Usage: /unadmin +1234567890"
        
        elif message_lower == '/help':
            return """🤖 Admin Commands:
/config - Show current configuration
/config reload - Reload config from file
/config enable/disable - Enable/disable bot
/config maintenance on/off - Toggle maintenance mode
/config whitelist on/off - Toggle whitelist mode
/config antiban on/off - Toggle anti-ban measures
/config tokens 500 - Set max response tokens
/config style brief - Set response style (conversational/brief/detailed)
/config model chat gpt-4o-mini - Set model for specific task
/allow +1234567890 - Add number to allowed list
/block +1234567890 - Add number to blocked list
/unblock +1234567890 - Remove number from blocked list
/admin +1234567890 - Add number to admin list
/unadmin +1234567890 - Remove number from admin list
/help - Show this help"""
        
        return None  # Not an admin command
    
    async def get_user_history(self, phone: str, limit: int = 10, db: Session = Depends(get_db)) -> List[ChatInteractionModel]:
        """
        Get conversation history for a user
        
        Args:
            phone: User's phone number
            limit: Maximum number of interactions to return
            db: Database session
            
        Returns:
            List[ChatInteractionModel]: List of chat interactions
        """
        user = db_manager.get_user_by_phone(db, phone)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get interactions from database
        interactions = db_manager.get_user_interactions(db, user.id, limit)
        
        # Convert DB models to Pydantic models
        result = []
        for interaction in interactions:
            chat_interaction = map_db_interaction_to_api_interaction(interaction)
            result.append(chat_interaction)
        
        return result
    
    async def get_anti_ban_stats(self) -> dict:
        """Get anti-ban related statistics"""
        return await self.anti_ban_service.get_conversation_stats()
    
    async def manual_opt_out(self, phone: str) -> dict:
        """Manually opt out a user"""
        await self.anti_ban_service._set_user_opted_out(phone)
        return {"status": "User opted out successfully"}
    
    async def anti_ban_health_check(self) -> dict:
        """Check anti-ban system health"""
        stats = await self.anti_ban_service.get_conversation_stats()
        return {
            "status": "healthy" if stats.get("rate_limit_status") == "healthy" else "warning",
            "stats": stats
        }

    async def redis_health_check(self) -> dict:
        """
        Check Redis health status
        
        Returns:
            dict: Redis health status and cache TTL
        """
        redis_status = "ok" if redis_cache.health_check() else "error"
        return {
            "status": redis_status,
            "cache_ttl_minutes": int(redis_cache.ttl / 60)
        }
    
    async def get_conversation_stats(self, phone: str, db: Session = Depends(get_db)) -> dict:
        """Get conversation statistics for a user"""
        user = db_manager.get_user_by_phone(db, phone)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        stats = self.conversation_service.get_conversation_stats(db, user.id)
        return stats
    
    async def force_conversation_summary(self, phone: str, language: str = None, 
                                       db: Session = Depends(get_db)) -> dict:
        """Force create a summary for a user's conversation"""
        user = db_manager.get_user_by_phone(db, phone)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        result = self.conversation_service.force_create_summary(db, user.id, language)
        return result 