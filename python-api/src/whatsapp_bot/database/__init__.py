"""
Database package for WhatsApp OpenAI Bot
"""

from whatsapp_bot.database.database import db_manager, init_db, get_db
from whatsapp_bot.database.models import Base, User, ChatInteraction, UsageLog
from whatsapp_bot.database.schema import ChatRequest, ChatResponse, ChatInteraction as ChatInteractionSchema
from whatsapp_bot.database.redis_cache import redis_cache 