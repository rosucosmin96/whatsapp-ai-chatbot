from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
from pydantic import BaseModel

from ..config import config_manager

class ResponseConfigUpdate(BaseModel):
    max_tokens: int = None
    min_tokens: int = None
    temperature: float = None
    response_style: str = None

class ModelConfigUpdate(BaseModel):
    default: str = None
    chat: str = None
    summarization: str = None
    translation: str = None
    analysis: str = None
    creative: str = None
    admin_commands: str = None

class AccessConfigUpdate(BaseModel):
    allowed_numbers: List[str] = None
    blocked_numbers: List[str] = None
    whitelist_mode: bool = None
    admin_numbers: List[str] = None

class BotConfigUpdate(BaseModel):
    enabled: bool = None
    maintenance_mode: bool = None
    maintenance_message: str = None

def create_config_router() -> APIRouter:
    """Create and configure configuration management routes"""
    router = APIRouter(tags=["config"])
    
    @router.get("/config")
    async def get_config():
        """Get current bot configuration"""
        return {
            "models": config_manager.config.models.__dict__,
            "response": config_manager.config.response.__dict__,
            "access": config_manager.config.access.__dict__,
            "anti_ban": config_manager.config.anti_ban.__dict__,
            "enabled": config_manager.config.enabled,
            "maintenance_mode": config_manager.config.maintenance_mode,
            "maintenance_message": config_manager.config.maintenance_message
        }
    
    @router.get("/config/summary")
    async def get_config_summary():
        """Get configuration summary"""
        return config_manager.get_config_summary()
    
    @router.post("/config/reload")
    async def reload_config():
        """Reload configuration from file"""
        config_manager.reload_config()
        return {"status": "Configuration reloaded successfully"}
    
    @router.put("/config/response")
    async def update_response_config(update: ResponseConfigUpdate):
        """Update response configuration"""
        update_dict = {k: v for k, v in update.dict().items() if v is not None}
        config_manager.update_response_config(**update_dict)
        return {"status": "Response configuration updated"}
    
    @router.put("/config/models")
    async def update_model_config(update: ModelConfigUpdate):
        """Update model configuration"""
        update_dict = {k: v for k, v in update.dict().items() if v is not None}
        config_manager.update_model_config(**update_dict)
        return {"status": "Model configuration updated"}
    
    @router.put("/config/access")
    async def update_access_config(update: AccessConfigUpdate):
        """Update access configuration"""
        update_dict = {k: v for k, v in update.dict().items() if v is not None}
        config_manager.update_access_config(**update_dict)
        return {"status": "Access configuration updated"}
    
    @router.put("/config/bot")
    async def update_bot_config(update: BotConfigUpdate):
        """Update general bot configuration"""
        if update.enabled is not None:
            config_manager.config.enabled = update.enabled
        if update.maintenance_mode is not None:
            config_manager.config.maintenance_mode = update.maintenance_mode
        if update.maintenance_message is not None:
            config_manager.config.maintenance_message = update.maintenance_message
        
        config_manager.save_config()
        return {"status": "Bot configuration updated"}
    
    @router.post("/config/numbers/allow/{phone}")
    async def add_allowed_number(phone: str):
        """Add a phone number to the allowed list"""
        config_manager.add_allowed_number(phone)
        return {"status": f"Added {phone} to allowed numbers"}
    
    @router.delete("/config/numbers/allow/{phone}")
    async def remove_allowed_number(phone: str):
        """Remove a phone number from the allowed list"""
        config_manager.remove_allowed_number(phone)
        return {"status": f"Removed {phone} from allowed numbers"}
    
    @router.post("/config/numbers/block/{phone}")
    async def add_blocked_number(phone: str):
        """Add a phone number to the blocked list"""
        config_manager.add_blocked_number(phone)
        return {"status": f"Added {phone} to blocked numbers"}
    
    @router.delete("/config/numbers/block/{phone}")
    async def remove_blocked_number(phone: str):
        """Remove a phone number from the blocked list"""
        config_manager.remove_blocked_number(phone)
        return {"status": f"Removed {phone} from blocked numbers"}
    
    @router.post("/config/numbers/admin/{phone}")
    async def add_admin_number(phone: str):
        """Add a phone number to the admin list"""
        config_manager.add_admin_number(phone)
        return {"status": f"Added {phone} to admin numbers"}
    
    @router.delete("/config/numbers/admin/{phone}")
    async def remove_admin_number(phone: str):
        """Remove a phone number from the admin list"""
        config_manager.remove_admin_number(phone)
        return {"status": f"Removed {phone} from admin numbers"}
    
    @router.get("/config/numbers/check/{phone}")
    async def check_number_access(phone: str):
        """Check if a phone number has access to the bot"""
        is_allowed = config_manager.is_number_allowed(phone)
        is_admin = config_manager.is_admin(phone)
        
        return {
            "phone": phone,
            "is_allowed": is_allowed,
            "is_admin": is_admin,
            "whitelist_mode": config_manager.config.access.whitelist_mode,
            "bot_enabled": config_manager.config.enabled
        }
    
    @router.post("/config/maintenance")
    async def set_maintenance_mode(enabled: bool, message: str = None):
        """Enable or disable maintenance mode"""
        config_manager.set_maintenance_mode(enabled, message)
        return {
            "status": f"Maintenance mode {'enabled' if enabled else 'disabled'}",
            "message": config_manager.config.maintenance_message
        }
    
    return router 