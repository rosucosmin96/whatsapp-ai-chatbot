import json
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
from .utils.logging_config import get_logger

logger = get_logger(__name__)

@dataclass
class ModelConfig:
    """Configuration for OpenAI models"""
    default: str = "gpt-4o-mini"
    chat: str = "gpt-4o-mini"
    summarization: str = "gpt-4o-mini"
    translation: str = "gpt-4o-mini"
    analysis: str = "gpt-4o-mini"
    creative: str = "gpt-4o-mini"
    admin_commands: str = "gpt-4o-mini"

@dataclass
class ResponseConfig:
    """Configuration for response generation"""
    max_tokens: int = 1000
    min_tokens: int = 50
    temperature: float = 0.8
    response_style: str = "conversational"  # conversational, brief, detailed
    
@dataclass
class AccessConfig:
    """Configuration for access control"""
    allowed_numbers: List[str] = None
    blocked_numbers: List[str] = None
    whitelist_mode: bool = False  # If True, only allowed_numbers can chat
    admin_numbers: List[str] = None
    
    def __post_init__(self):
        if self.allowed_numbers is None:
            self.allowed_numbers = []
        if self.blocked_numbers is None:
            self.blocked_numbers = []
        if self.admin_numbers is None:
            self.admin_numbers = []

@dataclass
class AntiBanConfig:
    """Configuration for anti-ban measures"""
    max_new_users_per_hour: int = 10
    min_reply_delay: float = 2.0
    max_reply_delay: float = 5.0
    global_rate_limit: float = 1.0
    daily_message_limits: Dict[int, int] = None
    
    def __post_init__(self):
        if self.daily_message_limits is None:
            self.daily_message_limits = {
                1: 20,   # Week 1: 20 messages/day
                2: 50,   # Week 2: 50 messages/day  
                3: 100,  # Week 3: 100 messages/day
                4: 200   # Week 4+: 200 messages/day
            }

@dataclass
class BotConfig:
    """Main bot configuration"""
    models: ModelConfig = None
    response: ResponseConfig = None
    access: AccessConfig = None
    anti_ban: AntiBanConfig = None
    enabled: bool = True
    maintenance_mode: bool = False
    maintenance_message: str = "Bot is currently under maintenance. Please try again later."
    
    def __post_init__(self):
        if self.models is None:
            self.models = ModelConfig()
        if self.response is None:
            self.response = ResponseConfig()
        if self.access is None:
            self.access = AccessConfig()
        if self.anti_ban is None:
            self.anti_ban = AntiBanConfig()

class ConfigManager:
    """Manager for bot configuration"""
    
    def __init__(self, config_path: str = "config/bot_config.json"):
        self.config_path = Path(config_path)
        self.config: BotConfig = BotConfig()
        self._ensure_config_dir()
        self.load_config()
    
    def _ensure_config_dir(self):
        """Ensure config directory exists"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
    
    def load_config(self) -> BotConfig:
        """Load configuration from file"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # Parse nested configurations
                response_config = ResponseConfig(**config_data.get('response', {}))
                access_config = AccessConfig(**config_data.get('access', {}))
                anti_ban_config = AntiBanConfig(**config_data.get('anti_ban', {}))
                models_config = ModelConfig(**config_data.get('models', {}))
                
                self.config = BotConfig(
                    models=models_config,
                    response=response_config,
                    access=access_config,
                    anti_ban=anti_ban_config,
                    enabled=config_data.get('enabled', True),
                    maintenance_mode=config_data.get('maintenance_mode', False),
                    maintenance_message=config_data.get('maintenance_message', 
                                                      "Bot is currently under maintenance. Please try again later.")
                )
                
                logger.info(f"Configuration loaded from {self.config_path}")
            else:
                # Create default config file
                self.save_config()
                logger.info(f"Created default configuration at {self.config_path}")
                
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            self.config = BotConfig()  # Use defaults
        
        return self.config
    
    def save_config(self):
        """Save current configuration to file"""
        try:
            config_dict = {
                'response': asdict(self.config.response),
                'access': asdict(self.config.access),
                'anti_ban': asdict(self.config.anti_ban),
                'enabled': self.config.enabled,
                'maintenance_mode': self.config.maintenance_mode,
                'maintenance_message': self.config.maintenance_message,
                'models': asdict(self.config.models)
            }
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Configuration saved to {self.config_path}")
            
        except Exception as e:
            logger.error(f"Error saving configuration: {str(e)}")
    
    def reload_config(self) -> BotConfig:
        """Reload configuration from file"""
        return self.load_config()
    
    def is_number_allowed(self, phone: str) -> bool:
        """Check if a phone number is allowed to use the bot"""
        # Remove any formatting from phone number
        clean_phone = phone.replace('+', '').replace('-', '').replace(' ', '')
        
        # Check if bot is enabled
        if not self.config.enabled:
            return False
        
        # Check if number is blocked
        for blocked in self.config.access.blocked_numbers:
            if clean_phone.endswith(blocked.replace('+', '').replace('-', '').replace(' ', '')):
                return False
        
        # If whitelist mode is enabled, only allowed numbers can chat
        if self.config.access.whitelist_mode:
            for allowed in self.config.access.allowed_numbers:
                if clean_phone.endswith(allowed.replace('+', '').replace('-', '').replace(' ', '')):
                    return True
            return False
        
        return True
    
    def is_admin(self, phone: str) -> bool:
        """Check if a phone number is an admin"""
        clean_phone = phone.replace('+', '').replace('-', '').replace(' ', '')
        
        for admin in self.config.access.admin_numbers:
            if clean_phone.endswith(admin.replace('+', '').replace('-', '').replace(' ', '')):
                return True
        return False
    
    def get_response_config(self) -> ResponseConfig:
        """Get response configuration"""
        return self.config.response
    
    def get_access_config(self) -> AccessConfig:
        """Get access configuration"""
        return self.config.access
    
    def get_anti_ban_config(self) -> AntiBanConfig:
        """Get anti-ban configuration"""
        return self.config.anti_ban
    
    def get_model_config(self) -> ModelConfig:
        """Get model configuration"""
        return self.config.models
    
    def update_response_config(self, **kwargs):
        """Update response configuration"""
        for key, value in kwargs.items():
            if hasattr(self.config.response, key):
                setattr(self.config.response, key, value)
        self.save_config()
    
    def update_access_config(self, **kwargs):
        """Update access configuration"""
        for key, value in kwargs.items():
            if hasattr(self.config.access, key):
                setattr(self.config.access, key, value)
        self.save_config()
    
    def update_model_config(self, **kwargs):
        """Update model configuration"""
        for key, value in kwargs.items():
            if hasattr(self.config.models, key):
                setattr(self.config.models, key, value)
        self.save_config()
    
    def add_allowed_number(self, phone: str):
        """Add a phone number to allowed list"""
        if phone not in self.config.access.allowed_numbers:
            self.config.access.allowed_numbers.append(phone)
            self.save_config()
            logger.info(f"Added {phone} to allowed numbers")
    
    def remove_allowed_number(self, phone: str):
        """Remove a phone number from allowed list"""
        if phone in self.config.access.allowed_numbers:
            self.config.access.allowed_numbers.remove(phone)
            self.save_config()
            logger.info(f"Removed {phone} from allowed numbers")
    
    def add_blocked_number(self, phone: str):
        """Add a phone number to blocked list"""
        if phone not in self.config.access.blocked_numbers:
            self.config.access.blocked_numbers.append(phone)
            self.save_config()
            logger.info(f"Added {phone} to blocked numbers")
    
    def remove_blocked_number(self, phone: str):
        """Remove a phone number from blocked list"""
        if phone in self.config.access.blocked_numbers:
            self.config.access.blocked_numbers.remove(phone)
            self.save_config()
            logger.info(f"Removed {phone} from blocked numbers")
    
    def add_admin_number(self, phone: str):
        """Add a phone number to admin list"""
        if phone not in self.config.access.admin_numbers:
            self.config.access.admin_numbers.append(phone)
            self.save_config()
            logger.info(f"Added {phone} to admin numbers")
    
    def remove_admin_number(self, phone: str):
        """Remove a phone number from admin list"""
        if phone in self.config.access.admin_numbers:
            self.config.access.admin_numbers.remove(phone)
            self.save_config()
            logger.info(f"Removed {phone} from admin numbers")
    
    def set_maintenance_mode(self, enabled: bool, message: str = None):
        """Enable or disable maintenance mode"""
        self.config.maintenance_mode = enabled
        if message:
            self.config.maintenance_message = message
        self.save_config()
        logger.info(f"Maintenance mode {'enabled' if enabled else 'disabled'}")
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get a summary of current configuration"""
        return {
            'bot_enabled': self.config.enabled,
            'maintenance_mode': self.config.maintenance_mode,
            'whitelist_mode': self.config.access.whitelist_mode,
            'allowed_numbers_count': len(self.config.access.allowed_numbers),
            'blocked_numbers_count': len(self.config.access.blocked_numbers),
            'admin_numbers_count': len(self.config.access.admin_numbers),
            'response_max_tokens': self.config.response.max_tokens,
            'response_style': self.config.response.response_style,
            'anti_ban_enabled': True,
            'max_new_users_per_hour': self.config.anti_ban.max_new_users_per_hour
        }

# Global config manager instance
config_manager = ConfigManager()

def get_model_for_task(task: str = None) -> str:
        """
        Get the appropriate model for a specific task
        
        Args:
            task: The task type (summarization, translation, etc.)
            
        Returns:
            Model name to use for the task
        """
        if config_manager and task:
            model_config = config_manager.get_model_config()
            return getattr(model_config, task, model_config.default)
        
        # Fallback to environment variable or default
        return os.getenv("OPENAI_MODEL", "gpt-4o-mini")