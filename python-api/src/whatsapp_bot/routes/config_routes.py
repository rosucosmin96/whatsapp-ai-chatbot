from fastapi import APIRouter, HTTPException, Depends
from typing import List
from pydantic import BaseModel
from sqlalchemy.orm import Session

from whatsapp_bot.config import config_manager, get_prompts_dir
from whatsapp_bot.database import db_manager, get_db

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

class PromptUpdate(BaseModel):
    system_prompt: str = None
    summary_prompt: str = None

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
    
    @router.get("/config/prompts/{language}")
    async def get_prompts_by_language(language: str):
        """Get system and summary prompts for a specific language"""
        prompts_dir = get_prompts_dir()
        
        # Define supported languages
        supported_languages = ["english", "romanian", "default"]
        
        if language not in supported_languages:
            raise HTTPException(
                status_code=400, 
                detail=f"Language '{language}' not supported. Available languages: {supported_languages}"
            )
        
        try:
            # Read system prompt
            system_prompt_file = prompts_dir / f"{language}.txt"
            if not system_prompt_file.exists():
                raise HTTPException(
                    status_code=404, 
                    detail=f"System prompt file not found for language '{language}'"
                )
            
            with open(system_prompt_file, 'r', encoding='utf-8') as f:
                system_prompt = f.read()
            
            # Read summary prompt
            summary_prompt_file = prompts_dir / f"summary_{language}.txt"
            summary_prompt = None
            
            if summary_prompt_file.exists():
                with open(summary_prompt_file, 'r', encoding='utf-8') as f:
                    summary_prompt = f.read()
            
            return {
                "language": language,
                "system_prompt": system_prompt,
                "summary_prompt": summary_prompt,
                "has_summary_prompt": summary_prompt is not None
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error reading prompt files: {str(e)}"
                        )
    
    @router.put("/config/prompt/{language}")
    async def update_prompts_by_language(language: str, prompt_update: PromptUpdate):
        """Update system and/or summary prompts for a specific language"""
        prompts_dir = get_prompts_dir()
        
        # Define supported languages
        supported_languages = ["english", "romanian", "default"]
        
        if language not in supported_languages:
            raise HTTPException(
                status_code=400, 
                detail=f"Language '{language}' not supported. Available languages: {supported_languages}"
            )
        
        try:
            updated_files = []
            
            # Update system prompt if provided
            if prompt_update.system_prompt is not None:
                system_prompt_file = prompts_dir / f"{language}.txt"
                with open(system_prompt_file, 'w', encoding='utf-8') as f:
                    f.write(prompt_update.system_prompt)
                updated_files.append(f"system prompt ({language}.txt)")
            
            # Update summary prompt if provided
            if prompt_update.summary_prompt is not None:
                summary_prompt_file = prompts_dir / f"summary_{language}.txt"
                with open(summary_prompt_file, 'w', encoding='utf-8') as f:
                    f.write(prompt_update.summary_prompt)
                updated_files.append(f"summary prompt (summary_{language}.txt)")
            
            if not updated_files:
                raise HTTPException(
                    status_code=400,
                    detail="No prompts provided. Please include system_prompt and/or summary_prompt in the request body."
                )
            
            return {
                "status": "Prompts updated successfully",
                "language": language,
                "updated_files": updated_files,
                "message": f"Updated {len(updated_files)} prompt file(s) for {language}"
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error updating prompt files: {str(e)}"
            )

    @router.delete("/config/erase/{phone}")
    async def erase_user_data(phone: str, db: Session = Depends(get_db)):
        """Erase all conversations/data for a user by phone number"""
        try:
            # Use the new method to erase all user data
            result = db_manager.erase_all_user_data(phone)
            
            if not result["user_found"]:
                raise HTTPException(
                    status_code=404,
                    detail=f"User with phone number {phone} not found"
                )
            
            return {
                "status": f"User data for {phone} erased successfully",
                "details": {
                    "interactions_deleted": result["interactions_deleted"],
                    "usage_logs_deleted": result["usage_logs_deleted"],
                    "user_deleted": result["user_deleted"],
                    "cache_cleared": result["cache_cleared"]
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error erasing user data: {str(e)}"
            )

    return router 