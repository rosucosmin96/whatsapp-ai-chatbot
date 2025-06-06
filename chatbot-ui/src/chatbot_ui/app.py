"""
WhatsApp OpenAI Bot - Chainlit UI Application

This is the main Chainlit application that provides a web-based chat interface
for the WhatsApp OpenAI Bot API.
"""

import chainlit as cl
from typing import Optional
from dotenv import load_dotenv
import logging
from config import Config

from chatbot_client import create_api_client, ChatbotAPIClient

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration - now using centralized config
API_BASE_URL = Config.API_BASE_URL
DEFAULT_PHONE = Config.DEFAULT_PHONE  
CHAINLIT_HOST = Config.CHAINLIT_HOST
CHAINLIT_PORT = Config.CHAINLIT_PORT

# Validate configuration on startup
if not Config.validate():
    logger.error("Configuration validation failed")
    exit(1)

# Optional: Print config for debugging
if Config.LOG_LEVEL == "DEBUG":
    Config.print_config()

# Global API client
api_client: Optional[ChatbotAPIClient] = None


async def initialize_api_client():
    """Initialize the global API client"""
    global api_client
    if api_client is None:
        api_client = create_api_client(API_BASE_URL)
        logger.info("API client initialized")


async def ensure_api_client():
    """Ensure the API client is available, reinitialize if needed"""
    global api_client
    if api_client is None:
        await initialize_api_client()
    return api_client


@cl.on_chat_start
async def start():
    """Initialize the chat session when a user starts chatting"""
    await initialize_api_client()

    # Get prompts from API
    client = await ensure_api_client()
    prompt_response = await client.get_prompts_by_language("english")
    system_prompt_default = prompt_response.system_prompt
    summary_prompt_default   = prompt_response.summary_prompt
    
    # Initialize chat settings
    settings = cl.ChatSettings([
        cl.input_widget.Select(
            id="language",
            label="🌐 Language",
            values=["english"],
            initial_index=0,
            description="Language for AI responses"
        ),
        cl.input_widget.TextInput(
            id="system_prompt",
            label="🤖 System Prompt",
            placeholder="You are a helpful AI assistant...",
            initial=system_prompt_default,
            description="Instructions that define the AI's behavior and personality"
        ),
        cl.input_widget.TextInput(
            id="summary_prompt",
            label="📝 Summary Prompt",
            placeholder="Summarize the following conversation...",
            initial=summary_prompt_default,
            description="Prompt used to generate conversation summaries"
        )
    ])
    
    await settings.send()
    
    # Welcome message with branding
    welcome_msg = """# 🤖 WhatsApp OpenAI Bot UI

Welcome! I'm your AI assistant powered by the WhatsApp OpenAI Bot backend.

**How it works:**
- Your messages are sent to the Python API backend
- The AI processes them with conversation history and context
- Responses include anti-ban measures and intelligent conversation management

**⚙️ Settings Available:**
Click the settings icon (⚙️) in the top-right corner to customize:
- Language settings
- System prompt to define AI behavior
- Summary prompt for conversation summaries

**Important:**
- The system prompt is used to define the AI's behavior and personality.
- The summary prompt is used to generate conversation summaries.
- The language settings are used to determine the language of the AI's responses.
- The phone number is used to identify the user and send messages to.
- The API base URL is used to connect to the Python API backend.
- After changing the settings, you need to click the "Save Settings" button to apply the changes.
- After applying the changes, the user data will be erased and the new settings will be applied.

Let's start chatting! 💬"""
    
    await cl.Message(
        content=welcome_msg,
        author="System"
    ).send()
    
    # Check API health
    await check_and_display_api_status()
    
    # Store initial settings in session
    phone = cl.user_session.get("phone_number") or DEFAULT_PHONE
    cl.user_session.set("phone_number", phone)
    cl.user_session.set("api_base_url", API_BASE_URL)
    cl.user_session.set("language", "english")
    cl.user_session.set("system_prompt", system_prompt_default)
    cl.user_session.set("summary_prompt", summary_prompt_default)
    cl.user_session.set("receiver_phone", "test")
    
    # Show session info
    session_info = f"""📱 **Session Information**
- Phone Number: `{phone}`
- API Endpoint: `{API_BASE_URL}`
- Language: English
- Status: Connected and ready

*You can modify these settings using the settings panel (⚙️)*"""
    
    await cl.Message(
        content=session_info,
        author="System"
    ).send()


@cl.on_settings_update
async def setup_agent(settings):
    """Handle settings updates"""
    language = settings.get("language", "english")
    # Update session variables with new settings
    client = await ensure_api_client()
    prompt_response = await client.get_prompts_by_language(language)
    system_prompt_default = prompt_response.system_prompt
    summary_prompt_default   = prompt_response.summary_prompt

    system_prompt = settings.get("system_prompt", system_prompt_default)
    summary_prompt = settings.get("summary_prompt", summary_prompt_default)

    # Update prompts in the backend API
    try:
        await client.update_prompts_by_language(language, system_prompt, summary_prompt)
        
        # Store in session
        cl.user_session.set("language", language)
        cl.user_session.set("system_prompt", system_prompt)
        cl.user_session.set("summary_prompt", summary_prompt)

        # Erase user data
        await client.erase_user_data(DEFAULT_PHONE)
        
        # Show confirmation message
        settings_summary = f"""⚙️ **Settings Updated**

🌐 **Language:** {language.title()}
🤖 **System Prompt:** `{system_prompt[:50]}{"..." if len(system_prompt) > 50 else ""}`
📝 **Summary Prompt:** `{summary_prompt[:50]}{"..." if len(summary_prompt) > 50 else ""}`

Settings have been applied and saved to the backend!"""
        
    except Exception as e:
        # If update fails, still store locally but show warning
        cl.user_session.set("language", language)
        cl.user_session.set("system_prompt", system_prompt)
        cl.user_session.set("summary_prompt", summary_prompt)
        
        settings_summary = f"""⚠️ **Settings Updated Locally**

🌐 **Language:** {language.title()}
🤖 **System Prompt:** `{system_prompt[:50]}{"..." if len(system_prompt) > 50 else ""}`
📝 **Summary Prompt:** `{summary_prompt[:50]}{"..." if len(summary_prompt) > 50 else ""}`

⚠️ Warning: Could not save to backend API: {str(e)}
Settings are applied locally for this session."""
    
    await cl.Message(
        content=settings_summary,
        author="System"
    ).send()


async def check_and_display_api_status():
    """Check API health and display status to user"""
    try:
        # Check general health
        client = await ensure_api_client()
        health_status = await client.get_health_status()
        
        if health_status.get("status") == "ok":
            status_msg = "✅ **API Status: Connected**"
                
        else:
            error_info = health_status.get("error", "Unknown error")
            status_msg = f"❌ **API Status: Connection Issues**\n\nError: {error_info}\n\nPlease ensure the Python API is running on {API_BASE_URL}"
        
        await cl.Message(
            content=status_msg,
            author="System"
        ).send()
        
    except Exception as e:
        error_msg = f"""❌ **API Status: Unavailable**

Could not connect to the backend API at `{API_BASE_URL}`

**Possible solutions:**
1. Ensure the Python API server is running
2. Check that the API_BASE_URL in .env is correct
3. Verify no firewall is blocking the connection

Error details: `{str(e)}`"""
        
        await cl.Message(
            content=error_msg,
            author="System"
        ).send()


@cl.on_message
async def main(message: cl.Message):
    """Handle incoming messages from users"""
    user_message = message.content
    phone = cl.user_session.get("phone_number", DEFAULT_PHONE)
    receiver_phone = cl.user_session.get("receiver_phone", "test")
    # Log the incoming message
    logger.info(f"Received message from UI user (phone: {phone}): {user_message[:100]}...")
    
    # Handle special commands
    if user_message.lower().startswith('//'):
        await handle_special_commands(user_message, phone)
        return
    
    # Process regular chat message
    await process_chat_message(user_message, phone, receiver_phone)


async def handle_special_commands(command: str, phone: str):
    """Handle special UI commands"""
    command_lower = command.lower().strip()
    
    if command_lower == '//status':
        await check_and_display_api_status()
    
    elif command_lower == '//history':
        await show_conversation_history(phone)
    
    elif command_lower.startswith('//phone '):
        new_phone = command[7:].strip()
        if new_phone:
            cl.user_session.set("phone_number", new_phone)
            await cl.Message(
                content=f"📱 Phone number updated to: `{new_phone}`\nFuture messages will use this number for API requests.\n\n*Tip: You can also update this in the settings panel (⚙️)*",
                author="System"
            ).send()
        else:
            await cl.Message(
                content="❌ Please provide a phone number. Usage: `/phone +1234567890`",
                author="System"
            ).send()
    
    elif command_lower == '//help':
        help_msg = """🔧 **Available Commands:**

`//status` - Check API connection and health status
`//history` - Show recent conversation history  
`//phone +1234567890` - Change phone number for API requests
`//info` - Show API information and endpoints
`//help` - Show this help message

**⚙️ Settings Panel:**
Click the settings icon (⚙️) in the top-right corner to customize:
- 🌐 Language settings
- 🤖 System prompt to define AI behavior
- 📝 Summary prompt for conversation summaries

**Important:**
- The system prompt is used to define the AI's behavior and personality.
- The summary prompt is used to generate conversation summaries.
- The language settings are used to determine the language of the AI's responses.
- The phone number is used to identify the user and send messages to.
- The API base URL is used to connect to the Python API backend.
- After changing the settings, you need to click the "Save Settings" button to apply the changes.
- After applying the changes, the user data will be erased and the new settings will be applied.

**Regular Usage:**
Just type your message normally and it will be sent to the AI assistant!"""
        
        await cl.Message(
            content=help_msg,
            author="System"
        ).send()
    
    elif command_lower == '//info':
        await show_api_info()
    
    else:
        await cl.Message(
            content=f"❓ Unknown command: `{command}`\nType `//help` to see available commands.",
            author="System"
        ).send()


async def show_conversation_history(phone: str):
    """Show recent conversation history for the user"""
    try:
        client = await ensure_api_client()
        history_data = await client.get_user_history(phone, limit=5)
        
        if "error" in history_data:
            await cl.Message(
                content=f"❌ Could not retrieve history: {history_data['error']}",
                author="System"
            ).send()
            return
        
        history = history_data.get("history", [])
        if not history:
            await cl.Message(
                content="📝 No conversation history found for this phone number.",
                author="System"
            ).send()
            return
        
        history_msg = f"📝 **Recent Conversation History** (Phone: {phone})\n\n"
        
        for i, interaction in enumerate(history[-5:], 1):  # Show last 5
            chat_request = interaction.get("chat_request", {})
            chat_response = interaction.get("chat_response", {})
            timestamp = interaction.get("timestamp", "")
            
            user_msg = chat_request.get("message", "No message")[:100]
            bot_response = chat_response.get("response", "No response")[:100]
            
            if len(user_msg) == 100:
                user_msg += "..."
            if len(bot_response) == 100:
                bot_response += "..."
            
            history_msg += f"**{i}.** *{timestamp}*\n"
            history_msg += f"👤 **You:** {user_msg}\n"
            history_msg += f"🤖 **Bot:** {bot_response}\n\n"
        
        await cl.Message(
            content=history_msg,
            author="System"
        ).send()
        
    except Exception as e:
        await cl.Message(
            content=f"❌ Error retrieving history: {str(e)}",
            author="System"
        ).send()


async def show_api_info():
    """Show API information and available endpoints"""
    try:
        client = await ensure_api_client()
        api_info = await client.get_api_info()
        
        if "error" in api_info:
            await cl.Message(
                content=f"❌ Could not retrieve API info: {api_info['error']}",
                author="System"
            ).send()
            return
        
        info_msg = f"""🔗 **API Information**

**Base URL:** `{API_BASE_URL}`
**Version:** {api_info.get('version', 'Unknown')}
**Description:** {api_info.get('message', 'WhatsApp OpenAI Bot API')}

**Available Endpoints:**"""
        
        endpoints = api_info.get('endpoints', {})
        if endpoints:
            for name, path in endpoints.items():
                info_msg += f"\n• `{name}`: {path}"
        
        features = api_info.get('features', [])
        if features:
            info_msg += "\n\n**Features:**"
            for feature in features:
                info_msg += f"\n• {feature}"
        
        await cl.Message(
            content=info_msg,
            author="System"
        ).send()
        
    except Exception as e:
        await cl.Message(
            content=f"❌ Error retrieving API info: {str(e)}",
            author="System"
        ).send()


async def process_chat_message(user_message: str, phone: str, receiver_phone: str = None):
    """Process a regular chat message through the API"""
    # Show processing indicator
    async with cl.Step(name="🤖 AI Assistant", type="run") as step:
        step.output = "Processing your message..."
        
        try:
            # Ensure API client is available
            client = await ensure_api_client()
            
            # Send message to API
            response_data = await client.send_message(phone, user_message, receiver_phone)
            bot_response = response_data.get("response", "I didn't receive a proper response.")
            
            step.output = "✅ Response received successfully!"
            
            # Log the response
            logger.info(f"AI response for {phone}: {bot_response[:100]}...")
            
        except Exception as e:
            step.output = f"❌ Error: {str(e)}"
            bot_response = f"""Sorry, I encountered an error while processing your message.

**Error details:** {str(e)}

**Troubleshooting:**
- Make sure the Python API is running on {API_BASE_URL}
- Check your internet connection
- Try again in a moment

If the problem persists, check the API logs for more details."""
            
            logger.error(f"Error processing message for {phone}: {str(e)}")
    
    # Send the bot's response
    await cl.Message(
        content=bot_response,
        author="AI Assistant"
    ).send()


@cl.on_stop
async def stop():
    """Clean up when the session ends"""
    global api_client
    if api_client:
        await api_client.close()
        api_client = None
        logger.info("API client connection closed")


@cl.on_chat_end
async def end():
    """Handle chat session end"""
    await stop()


if __name__ == "__main__":
    # This allows running the app directly with: python src/chatbot_ui/app.py
    import sys
    import subprocess
    
    # Run chainlit with this file
    cmd = ["chainlit", "run", __file__, "--port", str(CHAINLIT_PORT), "--host", CHAINLIT_HOST]
    subprocess.run(cmd) 