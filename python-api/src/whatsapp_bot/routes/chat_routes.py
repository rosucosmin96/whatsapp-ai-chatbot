from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from whatsapp_bot.database.schema import ChatRequest, ChatResponse, ChatInteraction as ChatInteractionModel
from whatsapp_bot.database import get_db
from whatsapp_bot.controllers.chat_controller import ChatController

def create_chat_router(chat_controller: ChatController) -> APIRouter:
    """Create and configure chat routes"""
    router = APIRouter(tags=["chat"])
    
    @router.post("/chat", response_model=ChatResponse)
    async def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
        """Handle chat interactions with users"""
        return await chat_controller.chat_endpoint(request, db)
    
    @router.get("/history/{phone}", response_model=List[ChatInteractionModel])
    async def get_user_history(
        phone: str, 
        receiver_phone: Optional[str] = Query(None, description="Filter by receiver phone number"),
        limit: int = Query(10, description="Maximum number of interactions to return"),
        db: Session = Depends(get_db)
    ):
        """Get conversation history for a user, optionally filtered by receiver phone"""
        return await chat_controller.get_user_history(phone, receiver_phone, limit, db)
    
    return router


def create_health_router(chat_controller: ChatController) -> APIRouter:
    """Create and configure health check routes"""
    router = APIRouter(tags=["health"])
    
    @router.get("/health")
    async def health_check():
        """General health check endpoint"""
        return {"status": "ok"}
    
    @router.get("/health/redis")
    async def redis_health_check():
        """Redis health check endpoint"""
        return await chat_controller.redis_health_check()
    
    @router.get("/health/anti-ban")
    async def anti_ban_health_check():
        """Anti-ban system health check endpoint"""
        return await chat_controller.anti_ban_health_check()
    
    return router


def create_anti_ban_router(chat_controller: ChatController) -> APIRouter:
    """Create and configure anti-ban management routes"""
    router = APIRouter(tags=["anti-ban"])
    
    @router.get("/anti-ban/stats")
    async def get_anti_ban_stats():
        """Get anti-ban statistics and rate limiting status"""
        return await chat_controller.get_anti_ban_stats()
    
    @router.post("/anti-ban/opt-out/{phone}")
    async def manual_opt_out(phone: str):
        """Manually opt out a user from receiving messages"""
        return await chat_controller.manual_opt_out(phone)
    
    @router.get("/conversation/stats/{phone}")
    async def get_conversation_stats(phone: str, db: Session = Depends(get_db)):
        """Get conversation statistics for a user"""
        return await chat_controller.get_conversation_stats(phone, db)
    
    @router.post("/conversation/force-summary/{phone}")
    async def force_conversation_summary(phone: str, language: str = None, db: Session = Depends(get_db)):
        """Force create a summary for a user's conversation"""
        return await chat_controller.force_conversation_summary(phone, language, db)
    
    return router 