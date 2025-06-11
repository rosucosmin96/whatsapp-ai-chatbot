import os
from openai import OpenAI
from dotenv import load_dotenv
from typing import Dict, Tuple, Optional, List, Any
from whatsapp_bot.utils.logging_config import get_logger
from whatsapp_bot.config import get_model_for_task, get_prompts_dir

# Load environment variables
load_dotenv()

logger = get_logger(__name__)

class OpenAIClient:
    def __init__(self, prompts_dir: Optional[str] = None):
        """
        Initialize OpenAI client with API key from environment
        
        Args:
            prompts_dir: Directory containing prompt files (will use absolute path if None)
        """
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Always use absolute path to prompts directory
        if prompts_dir is None:
            self.prompts_dir = get_prompts_dir()
        else:
            self.prompts_dir = prompts_dir
        
        logger.info(f"OpenAI client initialized with prompts directory: {self.prompts_dir}")
    
    def chat_completion(self, messages: List[Dict[str, str]], model: str = "gpt-3.5-turbo", 
                       temperature: float = 0.7, max_tokens: int = 1000) -> Tuple[str, Optional[Dict[str, Any]]]:
        """
        Get chat completion from OpenAI
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: OpenAI model to use
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens in response
            
        Returns:
            Tuple of (response_message, usage_info)
        """
        try:
            # Create the chat completion request
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Extract the response message
            response_message = response.choices[0].message.content
            
            # Extract usage information
            usage_info = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            
            logger.info(f"Chat completion successful - Model: {model}, Total tokens: {usage_info['total_tokens']}")
            
            return response_message, usage_info
            
        except Exception as e:
            logger.error(f"Error in OpenAI API call: {str(e)}")
            raise
    
    def detect_language(self, text: str) -> str:
        """
        Detect the language of the input text using OpenAI
        
        Args:
            text: Text to analyze
            
        Returns:
            Detected language code (e.g., 'english', 'romanian')
        """
        try:
            messages = [
                {
                    "role": "system", 
                    "content": """You are a language detection assistant. Respond with only the language name in lowercase. 
                    Supported languages: english, romanian, spanish, french, german, italian, portuguese, dutch, russian, chinese, japanese, korean, arabic, hebrew, hindi, turkish, polish, czech, hungarian, swedish, norwegian, danish, finnish.
                    If you cannot determine the language or it's not in the supported list, respond with 'english'."""
                },
                {
                    "role": "user", 
                    "content": f"What language is this text written in? Text: {text}"
                }
            ]
            
            response = self.client.chat.completions.create(
                model=get_model_for_task("translation"),
                messages=messages,
                max_tokens=15,
                temperature=0.0
            )
            
            detected_language = response.choices[0].message.content.strip().lower()
            logger.debug(f"Detected language: {detected_language}")
            
            # Common language mappings to handle variations
            language_mappings = {
                'romanian': 'romanian',
                'roma': 'romanian',
                'ro': 'romanian',
                'english': 'english', 
                'en': 'english',
                'spanish': 'spanish',
                'es': 'spanish',
                'french': 'french',
                'fr': 'french',
                'german': 'german',
                'de': 'german',
                'italian': 'italian',
                'it': 'italian',
                'portuguese': 'portuguese',
                'pt': 'portuguese',
                'dutch': 'dutch',
                'nl': 'dutch',
                'russian': 'russian',
                'ru': 'russian',
                'chinese': 'chinese',
                'zh': 'chinese'
            }
            
            # Normalize the detected language
            normalized_language = language_mappings.get(detected_language, detected_language)
            
            # Final validation - if not a known language, default to english
            common_languages = ['english', 'romanian', 'spanish', 'french', 'german', 'italian', 'portuguese', 'dutch', 'russian', 'chinese']
            if normalized_language not in common_languages:
                normalized_language = 'english'
                
            return normalized_language
            
        except Exception as e:
            logger.error(f"Error in language detection: {str(e)}")
            return 'english'  # Default fallback
    
    def load_system_prompt(self, language: str = 'english') -> str:
        """
        Load system prompt from file based on detected language
        
        Args:
            language: Language code (e.g., 'english', 'romanian')
            
        Returns:
            System prompt text
        """
        try:
            # Try to load the prompt file for the detected language
            prompt_file = os.path.join(self.prompts_dir, f"{language}.txt")
            
            if os.path.exists(prompt_file):
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    prompt = f.read().strip()
                logger.debug(f"Loaded system prompt for language: {language}")
                return prompt
            else:
                # Fallback to English if the language-specific file doesn't exist
                logger.warning(f"Prompt file for {language} not found, falling back to English")
                english_file = os.path.join(self.prompts_dir, "english.txt")
                if os.path.exists(english_file):
                    with open(english_file, 'r', encoding='utf-8') as f:
                        prompt = f.read().strip()
                    return prompt
                else:
                    # Ultimate fallback
                    return "You are a helpful assistant. Provide clear and accurate responses."
                    
        except Exception as e:
            logger.error(f"Error reading prompt file: {str(e)}")
            return "You are a helpful assistant. Provide clear and accurate responses."
    
    def generate_response(self, user_message: str, language: str = 'english', 
                         conversation_history: List[Dict[str, str]] = None, temperature: float = 0.7,
                         max_tokens: int = 2000, response_style: str = "conversational") -> str:
        """
        Generate a response using OpenAI with conversation history and configurable parameters
        
        Args:
            user_message: User's message
            language: Language for the response
            conversation_history: Previous conversation messages
            temperature: Sampling temperature for response variety (0.0-2.0)
            max_tokens: Maximum tokens in response
            response_style: Style of response (conversational, brief, detailed)
            
        Returns:
            Generated response message
        """
        try:
            # Load system prompt
            system_prompt = self.load_system_prompt(language)
            
            # Modify system prompt based on response style
            if response_style == "brief":
                system_prompt += "\n\nIMPORTANT: Keep your responses brief and concise. Aim for 1-2 sentences maximum unless more detail is specifically requested."
            elif response_style == "detailed":
                system_prompt += "\n\nIMPORTANT: Provide detailed, comprehensive responses with explanations and examples when appropriate."
            # conversational is the default, no modification needed
            
            # Build messages array
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add conversation history if provided
            if conversation_history:
                messages.extend(conversation_history)
            
            # Add current user message
            messages.append({"role": "user", "content": user_message})
            
            # Generate response with specified parameters
            response_message, _ = self.chat_completion(
                messages=messages,
                model=get_model_for_task("chat"),
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response_message
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            # Return a human-like fallback response
            fallback_responses = [
                "I'm having trouble understanding right now. Could you try rephrasing that?",
                "Sorry, I'm experiencing some technical difficulties. Can you try again?",
                "I'm not quite sure how to respond to that. Could you be more specific?",
                "Let me think about that... actually, could you ask that in a different way?"
            ]
            import random
            return random.choice(fallback_responses) 