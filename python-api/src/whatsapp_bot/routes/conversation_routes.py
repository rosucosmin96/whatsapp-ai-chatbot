from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Dict, Optional

from whatsapp_bot.database import get_db
from whatsapp_bot.controllers.chat_controller import ChatController

def create_conversation_router(chat_controller: ChatController) -> APIRouter:
    """Create and configure conversation management routes"""
    router = APIRouter(tags=["conversation"])
    
    @router.get("/conversation/stats/{phone}")
    async def get_conversation_stats(phone: str, db: Session = Depends(get_db)) -> Dict:
        """Get conversation statistics and token usage for a user"""
        return await chat_controller.get_conversation_stats(phone, db)
    
    @router.post("/conversation/force-summary/{phone}")
    async def force_conversation_summary(
        phone: str, 
        language: Optional[str] = Query(None, description="Language for summary (english/romanian)"),
        db: Session = Depends(get_db)
    ) -> Dict:
        """Force create a summary for a user's conversation"""
        return await chat_controller.force_conversation_summary(phone, language, db)
    
    return router 