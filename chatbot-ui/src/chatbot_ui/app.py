"""
WhatsApp OpenAI Bot - Chainlit UI Application

This is the main Chainlit application that provides a web-based chat interface
for the WhatsApp OpenAI Bot API.
"""

import chainlit as cl
import asyncio
import os
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv
import logging

from chatbot_client import create_api_client, ChatbotAPIClient

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
DEFAULT_PHONE = os.getenv("DEFAULT_PHONE", "+1234567890")  # Default phone for demo
CHAINLIT_HOST = os.getenv("CHAINLIT_HOST", "0.0.0.0")
CHAINLIT_PORT = int(os.getenv("CHAINLIT_PORT", "8080"))

# Global API client
api_client: Optional[ChatbotAPIClient] = None


async def initialize_api_client():
    """Initialize the global API client"""
    global api_client
    if api_client is None:
        api_client = create_api_client(API_BASE_URL)
        logger.info("API client initialized")


@cl.on_chat_start
async def start():
    """Initialize the chat session when a user starts chatting"""
    await initialize_api_client()
    
    # Initialize chat settings
    settings = cl.ChatSettings([
        cl.input_widget.TextInput(
            id="phone_number",
            label="📱 Phone Number",
            placeholder="+1234567890",
            initial=DEFAULT_PHONE,
            description="WhatsApp phone number for API requests"
        ),
        cl.input_widget.TextInput(
            id="api_base_url",
            label="🔗 API Base URL",
            placeholder="http://localhost:8000",
            initial=API_BASE_URL,
            description="Backend API endpoint URL"
        ),
        cl.input_widget.Select(
            id="response_style",
            label="🎭 Response Style",
            values=["casual", "formal", "friendly", "professional", "creative"],
            initial_index=2,
            description="AI response tone and style"
        ),
        cl.input_widget.Select(
            id="response_length",
            label="📝 Response Length",
            values=["short", "medium", "long", "auto"],
            initial_index=3,
            description="Preferred response length"
        ),
        cl.input_widget.Slider(
            id="creativity",
            label="🎨 Creativity Level",
            min=0.1,
            max=2.0,
            initial=1.0,
            step=0.1,
            description="AI creativity/randomness (temperature)"
        ),
        cl.input_widget.Switch(
            id="debug_mode",
            label="🐛 Debug Mode",
            initial=False,
            description="Show detailed API request/response information"
        ),
        cl.input_widget.Switch(
            id="auto_status_check",
            label="🔄 Auto Status Check",
            initial=True,
            description="Automatically check API health on startup"
        ),
        cl.input_widget.NumberInput(
            id="max_tokens",
            label="🔢 Max Tokens",
            initial=1000,
            min=100,
            max=4000,
            description="Maximum tokens for AI responses"
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
- Phone number and API endpoint
- Response style and length preferences  
- AI creativity level and token limits
- Debug mode and auto-status checks

Let's start chatting! 💬"""
    
    await cl.Message(
        content=welcome_msg,
        author="System"
    ).send()
    
    # Check API health if auto-check is enabled (default)
    if cl.user_session.get("auto_status_check", True):
        await check_and_display_api_status()
    
    # Store initial settings in session
    phone = cl.user_session.get("phone_number") or DEFAULT_PHONE
    cl.user_session.set("phone_number", phone)
    cl.user_session.set("api_base_url", API_BASE_URL)
    cl.user_session.set("response_style", "friendly")
    cl.user_session.set("response_length", "auto")
    cl.user_session.set("creativity", 1.0)
    cl.user_session.set("debug_mode", False)
    cl.user_session.set("auto_status_check", True)
    cl.user_session.set("max_tokens", 1000)
    
    # Show session info
    session_info = f"""📱 **Session Information**
- Phone Number: `{phone}`
- API Endpoint: `{API_BASE_URL}`
- Status: Connected and ready

*You can modify these settings using the settings panel (⚙️)*"""
    
    await cl.Message(
        content=session_info,
        author="System"
    ).send()


@cl.on_settings_update
async def setup_agent(settings):
    """Handle settings updates"""
    # Update session variables with new settings
    phone_number = settings.get("phone_number", DEFAULT_PHONE)
    api_base_url = settings.get("api_base_url", API_BASE_URL)
    response_style = settings.get("response_style", "friendly")
    response_length = settings.get("response_length", "auto")
    creativity = settings.get("creativity", 1.0)
    debug_mode = settings.get("debug_mode", False)
    auto_status_check = settings.get("auto_status_check", True)
    max_tokens = settings.get("max_tokens", 1000)
    
    # Store in session
    cl.user_session.set("phone_number", phone_number)
    cl.user_session.set("api_base_url", api_base_url)
    cl.user_session.set("response_style", response_style)
    cl.user_session.set("response_length", response_length)
    cl.user_session.set("creativity", creativity)
    cl.user_session.set("debug_mode", debug_mode)
    cl.user_session.set("auto_status_check", auto_status_check)
    cl.user_session.set("max_tokens", max_tokens)
    
    # Update global API client if URL changed
    global api_client
    if api_base_url != API_BASE_URL:
        try:
            if api_client:
                await api_client.close()
            api_client = create_api_client(api_base_url)
            logger.info(f"API client updated to use: {api_base_url}")
        except Exception as e:
            logger.error(f"Failed to update API client: {e}")
    
    # Show confirmation message
    settings_summary = f"""⚙️ **Settings Updated**

📱 **Phone Number:** `{phone_number}`
🔗 **API URL:** `{api_base_url}`
🎭 **Response Style:** {response_style.title()}
📝 **Response Length:** {response_length.title()}
🎨 **Creativity Level:** {creativity}
🔢 **Max Tokens:** {max_tokens}
🐛 **Debug Mode:** {"Enabled" if debug_mode else "Disabled"}
🔄 **Auto Status Check:** {"Enabled" if auto_status_check else "Disabled"}

Settings have been applied to your session!"""
    
    await cl.Message(
        content=settings_summary,
        author="System"
    ).send()
    
    # Auto-check API status if enabled and URL changed
    if auto_status_check and api_base_url != API_BASE_URL:
        await check_and_display_api_status()


async def check_and_display_api_status():
    """Check API health and display status to user"""
    try:
        # Check general health
        health_status = await api_client.get_health_status()
        
        if health_status.get("status") == "ok":
            status_msg = "✅ **API Status: Connected**\nBackend API is running and healthy."
            
            # Try to get additional health info
            try:
                redis_health = await api_client.get_redis_health()
                anti_ban_health = await api_client.get_anti_ban_health()
                
                status_details = []
                if redis_health.get("status") == "ok":
                    cache_ttl = redis_health.get("cache_ttl_minutes", "unknown")
                    status_details.append(f"🔄 Redis Cache: Healthy (TTL: {cache_ttl}min)")
                else:
                    status_details.append("⚠️ Redis Cache: Issues detected")
                
                if anti_ban_health.get("status") == "healthy":
                    status_details.append("🛡️ Anti-ban System: Active")
                else:
                    status_details.append("⚠️ Anti-ban System: Warning")
                
                if status_details:
                    status_msg += "\n\n**System Components:**\n" + "\n".join(status_details)
                    
            except Exception as e:
                logger.warning(f"Could not get detailed health status: {e}")
                
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
    debug_mode = cl.user_session.get("debug_mode", False)
    
    # Log the incoming message
    logger.info(f"Received message from UI user (phone: {phone}): {user_message[:100]}...")
    
    # Show debug info if enabled
    if debug_mode:
        debug_info = f"""🐛 **Debug Info - Incoming Message**
- Phone: `{phone}`
- Message Length: {len(user_message)} characters
- Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- Settings: Style={cl.user_session.get('response_style')}, Length={cl.user_session.get('response_length')}, Creativity={cl.user_session.get('creativity')}"""
        
        await cl.Message(
            content=debug_info,
            author="Debug"
        ).send()
    
    # Handle special commands
    if user_message.lower().startswith('/'):
        await handle_special_commands(user_message, phone)
        return
    
    # Process regular chat message
    await process_chat_message(user_message, phone)


async def handle_special_commands(command: str, phone: str):
    """Handle special UI commands"""
    command_lower = command.lower().strip()
    
    if command_lower == '/status':
        await check_and_display_api_status()
    
    elif command_lower == '/history':
        await show_conversation_history(phone)
    
    elif command_lower.startswith('/phone '):
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
    
    elif command_lower == '/help':
        help_msg = """🔧 **Available Commands:**

`/status` - Check API connection and health status
`/history` - Show recent conversation history  
`/phone +1234567890` - Change phone number for API requests
`/info` - Show API information and endpoints
`/test-text` - Demonstrate Chainlit text elements and formatting
`/help` - Show this help message

**⚙️ Settings Panel:**
Click the settings icon (⚙️) in the top-right corner to customize:
- 📱 Phone number and API endpoint
- 🎭 Response style (casual, formal, friendly, professional, creative)
- 📝 Response length preferences (short, medium, long, auto)
- 🎨 AI creativity level (0.1 - 2.0)
- 🔢 Maximum tokens for responses
- 🐛 Debug mode for detailed request/response info
- 🔄 Auto status checking on startup

**Regular Usage:**
Just type your message normally and it will be sent to the AI assistant!"""
        
        await cl.Message(
            content=help_msg,
            author="System"
        ).send()
    
    elif command_lower == '/info':
        await show_api_info()
    
    elif command_lower == '/test-text':
        await demonstrate_text_elements()
    
    else:
        await cl.Message(
            content=f"❓ Unknown command: `{command}`\nType `/help` to see available commands.",
            author="System"
        ).send()


async def show_conversation_history(phone: str):
    """Show recent conversation history for the user"""
    try:
        history_data = await api_client.get_user_history(phone, limit=5)
        
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
        api_info = await api_client.get_api_info()
        
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


async def demonstrate_text_elements():
    """Demonstrate various Chainlit text elements"""
    
    # 1. Basic Text Element attached to a message
    msg1 = cl.Message(
        content="Here's a basic **Text element** attached to this message:",
        author="Text Demo"
    )
    msg1.elements = [
        cl.Text(
            name="basic_text",
            content="This is a basic Chainlit Text element. It's useful for displaying simple text content that provides additional context or details.",
            display="inline"
        )
    ]
    await msg1.send()
    
    # 2. Text with side display mode
    msg2 = cl.Message(
        content="This message has a **side-panel text element**. Check the side panel!",
        author="Side Panel Demo"
    )
    msg2.elements = [
        cl.Text(
            name="side_text",
            content="This Text element uses 'side' display mode. It appears in a side panel, which is great for detailed information, documentation, or data that you want to keep accessible without cluttering the main chat.",
            display="side"
        )
    ]
    await msg2.send()
    
    # 3. Multiple messages with different authors
    await cl.Message(
        content="This is a regular **Message** element with markdown support and bold text!",
        author="Demo Bot"
    ).send()
    
    await cl.Message(
        content="`Code formatting` is also supported in messages.",
        author="Code Example"
    ).send()
    
    # 4. Message with multiple text elements
    msg3 = cl.Message(
        content="This message demonstrates **multiple text elements** attached to a single message:",
        author="Multi-Element Demo"
    )
    
    msg3.elements = [
        cl.Text(
            name="element_1",
            content="First text element: This contains primary information about the topic.",
            display="inline"
        ),
        cl.Text(
            name="element_2", 
            content="Second text element: This provides additional context and supplementary details.",
            display="inline"
        ),
        cl.Text(
            name="detailed_info",
            content="Detailed Information Panel: This text element contains comprehensive details that might be too long for the main message. It includes technical specifications, configuration options, and other detailed information that users can reference when needed.",
            display="side"
        )
    ]
    
    await msg3.send()
    
    # 5. Code block example
    code_example = '''```python
def hello_chainlit():
    """Example function for Chainlit text elements"""
    return "Hello from Chainlit!"

# This is how you can display code
result = hello_chainlit()
print(result)

# Text elements are great for:
# - API responses
# - Configuration data
# - Documentation
# - Debug information
```'''
    
    await cl.Message(
        content=f"Here's a **code block example**:\n\n{code_example}",
        author="Code Demo"
    ).send()
    
    # 6. Markdown formatting examples
    markdown_examples = """## Markdown Examples

### Text Formatting:
- **Bold text**
- *Italic text*  
- ~~Strikethrough text~~
- `Inline code`

### Lists:
1. Numbered list item 1
2. Numbered list item 2
   - Nested bullet point
   - Another nested item

### Links and Images:
- [Chainlit Documentation](https://docs.chainlit.io)
- You can also include tables and other markdown elements

### Blockquotes:
> This is a blockquote example
> It can span multiple lines

### Tables:
| Feature | Supported | Notes |
|---------|-----------|-------|
| Text Elements | ✅ | Attached to messages |
| Messages | ✅ | With authors |
| Markdown | ✅ | Full support |
| Code Blocks | ✅ | Syntax highlighting |
"""
    
    await cl.Message(
        content=markdown_examples,
        author="Markdown Demo"
    ).send()
    
    # 7. Long text content example with side panel
    msg4 = cl.Message(
        content="Here's an example of **long-form content** displayed in a side panel:",
        author="Long Content Demo"
    )
    
    long_text = """# Long Text Content Example

This is an example of displaying longer text content using Chainlit text elements.

## Use Cases for Text Elements:
- **Documentation and help content** - Provide detailed instructions
- **API responses and data** - Display structured information
- **Configuration information** - Show settings and parameters
- **Debug output and logs** - Technical information for troubleshooting
- **User instructions and tutorials** - Step-by-step guides

## Display Modes:
- **inline**: Shows the text inline with other content
- **side**: Shows the text in a side panel (useful for detailed info)
- **page**: Full page display (for very long content)

## Best Practices:
1. Use inline display for short, relevant information
2. Use side display for detailed information that supports the main message
3. Use page display for comprehensive documentation or very long content
4. Combine multiple text elements for organized information presentation

## Technical Details:
Text elements must be attached to messages using the `elements` property. They cannot be sent directly in newer versions of Chainlit.

Example:
```python
msg = cl.Message(content="Main message")
msg.elements = [
    cl.Text(name="detail", content="Details", display="side")
]
await msg.send()
```
"""
    
    msg4.elements = [
        cl.Text(
            name="long_content",
            content=long_text,
            display="side"
        )
    ]
    
    await msg4.send()
    
    # 8. Summary message
    summary_msg = """🎉 **Text Elements Demo Complete!**

You've now seen examples of:
- ✅ Text elements attached to messages
- ✅ Different display modes (inline, side)
- ✅ Multiple text elements per message
- ✅ Messages with various authors and markdown
- ✅ Code blocks and syntax highlighting
- ✅ Comprehensive markdown formatting
- ✅ Long-form content in side panels

**Key Takeaway:** Text elements must be attached to messages using the `elements` property - they cannot be sent directly.

**Try these patterns in your own Chainlit applications!**

*Use `/help` to see all available commands.*"""
    
    await cl.Message(
        content=summary_msg,
        author="Demo Summary"
    ).send()


async def process_chat_message(user_message: str, phone: str):
    """Process a regular chat message through the API"""
    # Get user settings
    response_style = cl.user_session.get("response_style", "friendly")
    response_length = cl.user_session.get("response_length", "auto")
    creativity = cl.user_session.get("creativity", 1.0)
    max_tokens = cl.user_session.get("max_tokens", 1000)
    debug_mode = cl.user_session.get("debug_mode", False)
    api_base_url = cl.user_session.get("api_base_url", API_BASE_URL)
    
    # Show processing indicator
    async with cl.Step(name="🤖 AI Assistant", type="run") as step:
        step.output = "Processing your message..."
        
        try:
            # Prepare enhanced message with style preferences
            enhanced_message = user_message
            if response_style != "auto":
                style_prompt = f" [Response style: {response_style}]"
                enhanced_message += style_prompt
            
            if response_length != "auto":
                length_prompt = f" [Response length: {response_length}]"
                enhanced_message += length_prompt
            
            # Show debug info if enabled
            if debug_mode:
                debug_request = f"""🐛 **Debug - API Request**
- API URL: `{api_base_url}`
- Original Message: `{user_message}`
- Enhanced Message: `{enhanced_message}`
- Settings Applied: Style={response_style}, Length={response_length}, Creativity={creativity}, MaxTokens={max_tokens}"""
                
                await cl.Message(
                    content=debug_request,
                    author="Debug"
                ).send()
            
            # Send message to API
            response_data = await api_client.send_message(phone, enhanced_message)
            bot_response = response_data.get("response", "I didn't receive a proper response.")
            
            step.output = "✅ Response received successfully!"
            
            # Show debug info for response if enabled
            if debug_mode:
                debug_response = f"""🐛 **Debug - API Response**
- Raw Response Length: {len(bot_response)} characters
- Response Preview: `{bot_response[:200]}{'...' if len(bot_response) > 200 else ''}`
- Processing Time: {datetime.now().strftime('%H:%M:%S')}"""
                
                await cl.Message(
                    content=debug_response,
                    author="Debug"
                ).send()
            
            # Log the response
            logger.info(f"AI response for {phone}: {bot_response[:100]}...")
            
        except Exception as e:
            step.output = f"❌ Error: {str(e)}"
            bot_response = f"""Sorry, I encountered an error while processing your message.

**Error details:** {str(e)}

**Troubleshooting:**
- Make sure the Python API is running on {api_base_url}
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