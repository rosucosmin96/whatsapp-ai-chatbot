import sys
import os
import uvicorn

# Check Python version
if sys.version_info < (3, 10):
    sys.exit("Error: This project requires Python 3.10 or higher")

from fastapi import FastAPI
from dotenv import load_dotenv

from whatsapp_bot.database import init_db
from whatsapp_bot.controllers.chat_controller import ChatController
from whatsapp_bot.routes import create_chat_router, create_health_router
from whatsapp_bot.routes.chat_routes import create_anti_ban_router
from whatsapp_bot.routes.config_routes import create_config_router
from whatsapp_bot.routes.conversation_routes import create_conversation_router
from whatsapp_bot.services.backup_service import DatabaseBackupService
from whatsapp_bot.utils.logging_config import setup_logging, get_logger
from whatsapp_bot.config import get_prompts_dir, get_config_path

# Load environment variables
load_dotenv()

# Initialize logging
log_level = os.getenv("LOG_LEVEL", "INFO")
setup_logging(log_level)
logger = get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="WhatsApp OpenAI Bot API",
    description="API for WhatsApp bot powered by OpenAI",
    version="1.0.0"
)

# Get absolute path to prompts directory
PROMPTS_DIR = get_prompts_dir()

# Ensure the necessary prompt files exist
default_prompts = {
    "english.txt": "You are a helpful WhatsApp assistant. Provide clear, concise, and accurate responses to user questions. Be friendly and polite in your interactions.",
    "romanian.txt": "Ești un asistent WhatsApp util. Oferă răspunsuri clare, concise și precise la întrebările utilizatorilor. Fii prietenos și politicos în interacțiunile tale.",
    "summary_english.txt": """Create a detailed summary of this conversation between user and assistant. 
                The summary should include all main topics, questions and answers, 
                and any important context for continuing the conversation.
                The summary should be in English.""",
    "summary_romanian.txt": """Creează un rezumat detaliat al acestei conversații între utilizator și asistent. 
                Rezumatul trebuie să includă toate subiectele principale, întrebările și răspunsurile, 
                și orice context important pentru continuarea conversației.
                Rezumatul trebuie să fie în limba română.""",
}

# Create prompts directory if it doesn't exist
PROMPTS_DIR.mkdir(parents=True, exist_ok=True)
logger.info(f"Using prompts directory: {PROMPTS_DIR.absolute()}")

# Create default prompt files if they don't exist
for filename, content in default_prompts.items():
    file_path = PROMPTS_DIR / filename
    if not file_path.exists():
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"Created default prompt file: {file_path}")

# Initialize controller with absolute prompts directory
chat_controller = ChatController(str(PROMPTS_DIR))

# Initialize database
try:
    init_db()
    logger.info("Database tables initialized")
except Exception as e:
    logger.error(f"Error initializing database: {str(e)}")

# Initialize backup service
try:
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        backup_service = DatabaseBackupService(database_url)
        backup_service.start_scheduler()
        logger.info("Automated backup service started")
    else:
        logger.warning("DATABASE_URL not set, backup service disabled")
except Exception as e:
    logger.warning(f"Could not start backup service: {str(e)}")

# Include routers
app.include_router(create_chat_router(chat_controller))
app.include_router(create_health_router(chat_controller))
app.include_router(create_anti_ban_router(chat_controller))
app.include_router(create_config_router())
app.include_router(create_conversation_router(chat_controller))

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "WhatsApp OpenAI Bot API with Configuration Management",
        "version": "1.1.0",
        "config": {
            "config_file": str(get_config_path()),
            "prompts_directory": str(PROMPTS_DIR.absolute())
        },
        "endpoints": {
            "chat": "/chat",
            "history": "/history/{phone}",
            "health": "/health",
            "redis_health": "/health/redis",
            "anti_ban_health": "/health/anti-ban",
            "anti_ban_stats": "/anti-ban/stats",
            "manual_opt_out": "/anti-ban/opt-out/{phone}",
            "conversation_stats": "/conversation/stats/{phone}",
            "force_summary": "/conversation/force-summary/{phone}",
            "config": "/config",
            "config_summary": "/config/summary",
            "update_response": "/config/response",
            "update_models": "/config/models",
            "update_access": "/config/access",
            "manage_numbers": "/config/numbers/allow/{phone}",
            "maintenance_mode": "/config/maintenance"
        },
        "features": [
            "Human-like response delays",
            "Rate limiting and warm-up periods", 
            "Spam detection and content filtering",
            "User opt-out management",
            "Conversation summarization",
            "Anti-ban monitoring",
            "Configuration management",
            "Model configuration per task",
            "Access control (whitelist/blacklist)",
            "Response length and style control",
            "Admin commands via WhatsApp",
            "Maintenance mode"
        ]
    }


def start_app():
    """Entry point for starting the API server"""
    logger.info("Starting WhatsApp OpenAI Bot API server")
    
    # Disable reload in production, enable in development
    reload_mode = os.getenv("RELOAD_MODE", "false").lower() == "true"
    
    uvicorn_config = {
        "app": "whatsapp_bot.main:app",
        "host": "0.0.0.0",
        "port": 8000,
        "reload": reload_mode
    }
    
    # If reload is enabled, configure what to watch
    if reload_mode:
        uvicorn_config.update({
            "reload_dirs": ["src/whatsapp_bot"],  # Only watch source code
            "reload_excludes": [
                "*.log",
                "*.sql", 
                "backups/*",
                "logs/*",
                "__pycache__/*",
                "*.pyc"
            ]
        })
    
    uvicorn.run(**uvicorn_config)

if __name__ == "__main__":
    start_app()