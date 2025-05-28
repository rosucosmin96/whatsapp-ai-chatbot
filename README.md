# 🤖 WhatsApp OpenAI Bot

A production-ready WhatsApp chatbot powered by OpenAI GPT, featuring conversation history, Redis caching, and automated database backups.

## 🏗️ Architecture

```
WhatsApp Message → Node.js Bot → Python API → OpenAI GPT → Response
                                     ↓
                              PostgreSQL + Redis Cache
```

**Tech Stack:**
- **Frontend**: WhatsApp Web automation via `whatsapp-web.js`
- **Backend**: FastAPI (Python) with MVC architecture
- **AI**: OpenAI GPT-3.5/GPT-4 integration
- **Database**: PostgreSQL for persistent storage
- **Cache**: Redis for conversation history (30-min TTL)
- **Backup**: Automated hourly database backups

## 📂 Project Structure

```
whatsapp-openai-bot/
├── node-bot/                          # WhatsApp automation
│   ├── app.js                         # Main WhatsApp listener
│   ├── config.js                      # API configuration
│   ├── package.json                   # Node.js dependencies
│   └── .env                           # Environment variables
│
├── python-api/                        # FastAPI backend
│   ├── src/whatsapp_bot/              # Main application
│   │   ├── main.py                    # FastAPI app entry point
│   │   ├── controllers/               # Business logic
│   │   │   └── chat_controller.py     # Chat operations
│   │   ├── routes/                    # API endpoints
│   │   │   └── chat_routes.py         # Route definitions
│   │   ├── database/                  # Data layer
│   │   │   ├── models.py              # SQLAlchemy models
│   │   │   ├── schema.py              # Pydantic schemas
│   │   │   ├── database.py            # DB operations
│   │   │   └── redis_cache.py         # Redis cache manager
│   │   ├── services/                  # External services
│   │   │   └── backup_service.py      # Automated backups
│   │   ├── openai_client.py           # OpenAI integration
│   │   └── mapper.py                  # Data mapping
│   ├── prompts/                       # AI system prompts
│   │   ├── english.txt                # English prompts
│   │   └── romanian.txt               # Romanian prompts
│   ├── backups/                       # Database backups
│   ├── requirements.txt               # Python dependencies
│   ├── pyproject.toml                 # Project configuration
│   └── .env                           # Environment variables
│
├── README.md                          # This file
└── SETUP.md                           # Detailed setup guide
```

## 🚀 Quick Start

### Prerequisites
- **Python 3.10+** (Required)
- **Node.js 18+**
- **PostgreSQL 13+**
- **Redis 6+**
- **OpenAI API Key**

### 1. Clone Repository
```bash
git clone <repository-url>
cd whatsapp-openai-bot
```

### 2. Setup Backend
```bash
cd python-api
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Setup Database & Redis
```bash
# Install and start PostgreSQL
brew install postgresql redis  # macOS
brew services start postgresql redis

# Create database
psql postgres -c "CREATE DATABASE chatbot_db;"
psql postgres -c "CREATE USER chatbot_user WITH PASSWORD 'your_password';"
psql postgres -c "GRANT ALL PRIVILEGES ON DATABASE chatbot_db TO chatbot_user;"
```

### 4. Configure Environment
```bash
# Create .env file in python-api/
cat > .env << EOF
OPENAI_API_KEY=sk-your-openai-api-key
DATABASE_URL=postgresql://chatbot_user:your_password@localhost:5432/chatbot_db
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
PROMPTS_DIR=prompts
EOF
```

### 5. Start Services
```bash
# Terminal 1: Start Python API
cd python-api
python -m src.whatsapp_bot.main

# Terminal 2: Start WhatsApp Bot
cd node-bot
npm install
node app.js
```

### 6. Connect WhatsApp
Scan the QR code with your WhatsApp mobile app.

## 🧪 Testing

### API Health Checks
```bash
# General health
curl http://localhost:8000/health

# Redis health
curl http://localhost:8000/health/redis

# API documentation
open http://localhost:8000/docs
```

### Chat Interaction
```bash
# Send a message
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+1234567890",
    "message": "Hello, how are you?"
  }'

# Get conversation history
curl "http://localhost:8000/history/+1234567890?limit=5"
```

### Redis Cache Inspection
```bash
# List all keys
redis-cli KEYS "*"

# View user conversation
redis-cli LRANGE "user:1:conversations" 0 -1

# Check TTL
redis-cli TTL "user:1:conversations"
```

### Database Inspection
```bash
# Connect to database
psql -U chatbot_user -d chatbot_db

# View tables
\dt

# Check users
SELECT * FROM users;

# Check interactions
SELECT * FROM chat_interactions ORDER BY created_at DESC LIMIT 5;
```

## 🔄 Automated Backups

The system includes automated hourly database backups:

### Backup Features
- **Frequency**: Every hour
- **Location**: `python-api/backups/`
- **Format**: SQL dump files
- **Naming**: `backup_YYYY-MM-DD_HH-MM-SS.sql`
- **Retention**: Configurable (default: 2 hours)

### Manual Backup
```bash
# Create backup
python -m src.whatsapp_bot.services.backup_service

# Restore from backup
psql -U chatbot_user -d chatbot_db -f backups/backup_2024-01-15_14-30-00.sql
```

## 📊 Features

### Core Features
- ✅ **Multi-language Support** (English, Romanian)
- ✅ **Conversation History** (PostgreSQL + Redis cache)
- ✅ **Intelligent Conversation Summarization** (Automatic context optimization)
- ✅ **Anti-Ban Protection** (Human-like behavior and rate limiting)
- ✅ **Language Detection** (Automatic)
- ✅ **Error Handling** (Graceful fallbacks)
- ✅ **Health Monitoring** (API endpoints)
- ✅ **Automated Backups** (Hourly schedule)

### Technical Features
- ✅ **MVC Architecture** (Controllers, Routes, Services)
- ✅ **Redis Caching** (30-minute conversation TTL)
- ✅ **Token Management** (Automatic conversation optimization)
- ✅ **Database Migrations** (SQLAlchemy)
- ✅ **API Documentation** (FastAPI auto-docs)
- ✅ **Environment Configuration** (.env files)
- ✅ **Logging** (Structured logging)

## 🧠 Conversation Summarization

The bot includes intelligent conversation summarization to manage long conversations efficiently:

### How It Works
1. **Token Monitoring**: Tracks conversation length using tiktoken
2. **Automatic Triggering**: When conversation exceeds `SUMMARY_TRIGGER_TOKENS` (default: 2500)
3. **Smart Summarization**: Creates detailed summaries preserving context and user preferences
4. **Context Optimization**: Keeps recent messages + summary for continued natural conversation
5. **Multi-language Support**: Summary prompts available in English and Romanian

### Configuration
```bash
# Conversation Summarization Configuration
MAX_CONTEXT_TOKENS=3000
SUMMARY_TRIGGER_TOKENS=2500
SUMMARY_TARGET_TOKENS=800
KEEP_RECENT_MESSAGES=4

# Anti-Ban Configuration
MAX_NEW_USERS_PER_HOUR=10
MIN_REPLY_DELAY=2.0
MAX_REPLY_DELAY=5.0
GLOBAL_RATE_LIMIT=1.0

# Backup Configuration
BACKUP_RETENTION_HOURS=2
BACKUP_SCHEDULE_HOURS=1
```

### API Endpoints
```bash
# Get conversation statistics
curl "http://localhost:8000/conversation/stats/+1234567890"

# Force create summary (for testing)
curl -X POST "http://localhost:8000/conversation/force-summary/+1234567890?language=english"
```

### Benefits
- **Cost Optimization**: Reduces OpenAI API token usage by 60-80%
- **Performance**: Faster response times with optimized context
- **Context Preservation**: Maintains conversation flow and user preferences
- **Scalability**: Handles unlimited conversation length

## 🛡️ Anti-Ban Protection

The bot includes comprehensive anti-ban measures to prevent WhatsApp account suspension:

### Safety Features
1. **Human-like Delays**: Random response delays (2-5 seconds) with time-of-day variation
2. **Rate Limiting**: Global message rate limiting and new user restrictions
3. **Gradual Warm-up**: Progressive daily message limits for new deployments
4. **Spam Detection**: Content filtering for promotional language and excessive links
5. **User Opt-out**: Automatic detection and handling of unsubscribe requests
6. **Response Sanitization**: Removes promotional language and adds human imperfections

### Warm-up Schedule
```
Week 1: 20 messages/day
Week 2: 50 messages/day  
Week 3: 100 messages/day
Week 4+: 200 messages/day
```

### Configuration
```bash
# Anti-Ban Configuration
MAX_NEW_USERS_PER_HOUR=10      # Limit new user conversations per hour
MIN_REPLY_DELAY=2.0            # Minimum delay before responding (seconds)
MAX_REPLY_DELAY=5.0            # Maximum delay before responding (seconds)
GLOBAL_RATE_LIMIT=1.0          # Minimum time between any messages (seconds)
```

### API Endpoints
```bash
# Get anti-ban statistics
curl "http://localhost:8000/anti-ban/stats"

# Check anti-ban system health
curl "http://localhost:8000/health/anti-ban"

# Manually opt out a user
curl -X POST "http://localhost:8000/anti-ban/opt-out/+1234567890"
```

### Safety Guidelines
- **Only respond to incoming messages** (never initiate conversations)
- **Respect user opt-outs** (automatic detection of "stop", "unsubscribe", etc.)
- **Monitor daily limits** (automatic enforcement with graceful degradation)
- **Use varied responses** (higher temperature for natural variation)
- **Avoid spam patterns** (automatic content filtering)

### Monitoring
The system provides real-time monitoring of:
- Daily message counts vs. limits
- New user rate limiting status
- Opt-out user tracking
- Rate limit health status
- Response delay statistics

## 🔧 Configuration

### Environment Variables

#### Python API (.env)
```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-your-api-key
OPENAI_MODEL=gpt-3.5-turbo

# Database Configuration
DATABASE_URL=postgresql://user:pass@localhost:5432/db

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# Application Configuration
PROMPTS_DIR=prompts
LOG_LEVEL=INFO

# Conversation Summarization Configuration
MAX_CONTEXT_TOKENS=3000
SUMMARY_TRIGGER_TOKENS=2500
SUMMARY_TARGET_TOKENS=800
KEEP_RECENT_MESSAGES=4

# Anti-Ban Configuration
MAX_NEW_USERS_PER_HOUR=10
MIN_REPLY_DELAY=2.0
MAX_REPLY_DELAY=5.0
GLOBAL_RATE_LIMIT=1.0

# Backup Configuration
BACKUP_RETENTION_HOURS=2
BACKUP_SCHEDULE_HOURS=1
```

## 🔧 Configuration Management

The bot includes a comprehensive configuration system that allows admins to control bot behavior without code changes:

### Configuration File
The bot uses a JSON configuration file located at `config/bot_config.json`:

```json
{
  "response": {
    "max_tokens": 1000,
    "min_tokens": 50,
    "temperature": 0.8,
    "response_style": "conversational"
  },
  "access": {
    "allowed_numbers": ["+1234567890"],
    "blocked_numbers": [],
    "whitelist_mode": false,
    "admin_numbers": ["+1234567890"]
  },
  "anti_ban": {
    "max_new_users_per_hour": 10,
    "min_reply_delay": 2.0,
    "max_reply_delay": 5.0,
    "global_rate_limit": 1.0
  },
  "enabled": true,
  "maintenance_mode": false,
  "maintenance_message": "Bot is currently under maintenance."
}
```

### Response Configuration
Control how the bot generates responses:

- **max_tokens**: Maximum response length (50-4000)
- **temperature**: Response creativity (0.0-2.0)
- **response_style**: Response style options:
  - `conversational` - Natural, friendly responses
  - `brief` - Short, concise responses (1-2 sentences)
  - `detailed` - Comprehensive responses with explanations

### Access Control
Manage who can use the bot:

- **allowed_numbers**: List of phone numbers that can chat with the bot
- **blocked_numbers**: List of phone numbers that are blocked
- **whitelist_mode**: If `true`, only allowed_numbers can chat
- **admin_numbers**: Phone numbers with admin privileges

### Admin Commands via WhatsApp
Admins can control the bot directly through WhatsApp messages:

```
/help - Show available commands
/config - Show current configuration
/config reload - Reload config from file
/config enable/disable - Enable/disable bot
/config maintenance on/off - Toggle maintenance mode
/config whitelist on/off - Toggle whitelist mode
/config tokens 500 - Set max response tokens
/config style brief - Set response style
/allow +1234567890 - Add number to allowed list
/block +1234567890 - Add number to blocked list
/unblock +1234567890 - Remove from blocked list
/admin +1234567890 - Add number to admin list
/unadmin +1234567890 - Remove from admin list
```

### API Endpoints for Configuration

#### Get Configuration
```bash
# Get full configuration
curl "http://localhost:8000/config"

# Get configuration summary
curl "http://localhost:8000/config/summary"
```

#### Update Response Settings
```bash
# Set response length and style
curl -X PUT "http://localhost:8000/config/response" \
  -H "Content-Type: application/json" \
  -d '{
    "max_tokens": 500,
    "response_style": "brief",
    "temperature": 0.9
  }'
```

#### Manage Access Control
```bash
# Add allowed number
curl -X POST "http://localhost:8000/config/numbers/allow/+1234567890"

# Block a number
curl -X POST "http://localhost:8000/config/numbers/block/+9876543210"

# Add admin number
curl -X POST "http://localhost:8000/config/numbers/admin/+1234567890"

# Remove admin number
curl -X DELETE "http://localhost:8000/config/numbers/admin/+1234567890"

# Check number access
curl "http://localhost:8000/config/numbers/check/+1234567890"

# Enable whitelist mode
curl -X PUT "http://localhost:8000/config/access" \
  -H "Content-Type: application/json" \
  -d '{"whitelist_mode": true}'
```

#### Maintenance Mode
```bash
# Enable maintenance mode
curl -X POST "http://localhost:8000/config/maintenance?enabled=true&message=Under maintenance"

# Disable maintenance mode
curl -X POST "http://localhost:8000/config/maintenance?enabled=false"
```

### Configuration Features
- **Hot Reload**: Changes take effect immediately without restart
- **Validation**: Input validation prevents invalid configurations
- **Persistence**: All changes are automatically saved to file
- **Admin Control**: Full control via WhatsApp commands or API
- **Access Logging**: All configuration changes are logged