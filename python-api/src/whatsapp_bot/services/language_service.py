from typing import Optional
from whatsapp_bot.openai_client import OpenAIClient
from whatsapp_bot.config import config_manager
from whatsapp_bot.utils.logging_config import get_logger

logger = get_logger(__name__)

class LanguageDetectionService:
    """Service for detecting and managing message languages"""
    
    def __init__(self):
        self.client = OpenAIClient()
        self.config_manager = config_manager
    
    def detect_language(self, text: str) -> str:
        """
        Detect the language of the input text
        
        Args:
            text: Text to analyze for language detection
            
        Returns:
            Detected language code (e.g., 'english', 'romanian', 'spanish')
        """
        language_config = self.config_manager.get_language_config()
        
        # If language detection is disabled, return default language
        if not language_config.detection_enabled:
            logger.debug(f"Language detection disabled, using default: {language_config.default_language}")
            return language_config.default_language
        
        # Skip detection for very short texts (likely not informative enough)
        if len(text.strip()) < 10:
            logger.debug(f"Text too short for reliable detection, using default: {language_config.default_language}")
            return language_config.default_language
        
        try:
            detected_language = self.client.detect_language(text)
            logger.info(f"Language detected: {detected_language}")
            return detected_language
            
        except Exception as e:
            logger.error(f"Error in language detection: {str(e)}")
            return language_config.default_language
    
    def get_language_for_conversation(self, text: str, user_id: Optional[int] = None) -> str:
        """
        Get the appropriate language for a conversation
        
        Args:
            text: Current message text
            user_id: Optional user ID for future language preference storage
            
        Returns:
            Language code to use for the response
        """
        # For now, detect language from current message
        # In future, could implement user language preference storage
        detected_language = self.detect_language(text)
        
        # Additional validation - ensure we have prompts for this language
        supported_languages = self._get_supported_languages()
        
        if detected_language not in supported_languages:
            logger.warning(f"Language {detected_language} not supported, falling back to default")
            return self.config_manager.get_language_config().default_language
        
        return detected_language
    
    def _get_supported_languages(self) -> list:
        """
        Get list of supported languages based on available prompt files
        
        Returns:
            List of supported language codes
        """
        import os
        from pathlib import Path
        
        # Check what prompt files are available
        prompts_dir = os.getenv("PROMPTS_DIR", "prompts")
        supported_languages = []
        
        try:
            if os.path.exists(prompts_dir):
                for file in os.listdir(prompts_dir):
                    if file.endswith('.txt') and not file.startswith('summary_'):
                        language = file.replace('.txt', '')
                        supported_languages.append(language)
            
            # Ensure default language is always supported
            default_lang = self.config_manager.get_language_config().default_language
            if default_lang not in supported_languages:
                supported_languages.append(default_lang)
                
        except Exception as e:
            logger.error(f"Error checking supported languages: {str(e)}")
            # Fallback to common languages
            supported_languages = ['english', 'romanian']
        
        logger.debug(f"Supported languages: {supported_languages}")
        return supported_languages
    
    def is_language_detection_enabled(self) -> bool:
        """Check if language detection is enabled"""
        return self.config_manager.get_language_config().detection_enabled
    
    def get_default_language(self) -> str:
        """Get the default language"""
        return self.config_manager.get_language_config().default_language
