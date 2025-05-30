# 🛠️ Local Development Setup

A simple guide to set up the WhatsApp OpenAI Bot for local development on your machine.

## 📋 Prerequisites

- **Python 3.10+** 
- **Node.js 18+**
- **PostgreSQL**
- **Redis**
- **OpenAI API Key** (from [OpenAI Platform](https://platform.openai.com/))

## 🖥️ Platform-Specific Installation

### macOS (Homebrew)

```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install all dependencies
brew install python@3.11 node postgresql redis

# Start services
brew services start postgresql
brew services start redis

# Verify installations
python3 --version
node --version
psql --version
redis-cli ping
```

### Ubuntu/Debian

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-pip

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Install PostgreSQL and Redis
sudo apt install -y postgresql postgresql-contrib redis-server

# Start services
sudo systemctl start postgresql redis-server
sudo systemctl enable postgresql redis-server
```

### Windows

```powershell
# Using Chocolatey (install from https://chocolatey.org/)
choco install python311 nodejs postgresql redis-64 -y

# Start services
net start postgresql-x64-14
net start redis
```

## 📦 Project Setup

### 1. Clone Repository

```bash
git clone <your-repository-url>
cd whatsapp-openai-bot
```

### 2. Python API Setup

```bash
# Navigate to Python API
cd python-api

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate    # Windows

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Database Setup

```bash
# Create database and user
sudo -u postgres psql << EOF
CREATE DATABASE chatbot_db;
CREATE USER chatbot_user WITH PASSWORD 'dev_password';
GRANT ALL PRIVILEGES ON DATABASE chatbot_db TO chatbot_user;
\q
EOF

# Test connection
psql -U chatbot_user -d chatbot_db -h localhost -c "SELECT version();"
```

### 4. Environment Configuration

Create `.env` file in `python-api/`:

```bash
cat > .env << EOF
# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-3.5-turbo

# Database Configuration
DATABASE_URL=postgresql://chatbot_user:dev_password@localhost:5432/chatbot_db

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Development Configuration
PROMPTS_DIR=prompts
LOG_LEVEL=DEBUG

# Anti-Ban Configuration (relaxed for development)
MAX_NEW_USERS_PER_HOUR=50
MIN_REPLY_DELAY=1.0
MAX_REPLY_DELAY=2.0
GLOBAL_RATE_LIMIT=0.5
EOF
```

### 5. Node.js Bot Setup

```bash
# Navigate to Node.js bot
cd ../node-bot

# Install dependencies
npm install

# Create .env file
cat > .env << EOF
API_URL=http://localhost:8000
EOF
```

## 🚀 Running the Application

### Start Python API

```bash
cd python-api
source venv/bin/activate
python -m src.whatsapp_bot.main
```

### Start Node.js Bot (new terminal)

```bash
cd node-bot
node app.js
```

### Connect WhatsApp

1. Scan the QR code displayed in the Node.js terminal
2. Open WhatsApp on your phone
3. Go to Settings > Linked Devices > Link a Device
4. Scan the QR code

## 🧪 Development Testing

### API Health Check

```bash
# Test API
curl http://localhost:8000/health

# Test Redis
curl http://localhost:8000/health/redis

# View API docs
open http://localhost:8000/docs
```

### Send Test Message

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+1234567890",
    "message": "Hello bot!"
  }'
```

### Database Inspection

```bash
# Connect to database
psql -U chatbot_user -d chatbot_db -h localhost

# View tables
\dt

# Check data
SELECT * FROM users LIMIT 5;
SELECT * FROM chat_interactions ORDER BY created_at DESC LIMIT 5;
\q
```

### Redis Cache Check

```bash
# List all keys
redis-cli KEYS "*"

# View conversation
redis-cli LRANGE "user:1:conversations" 0 -1

# Clear cache (if needed)
redis-cli FLUSHALL
```

## 🔧 Development Configuration

### Bot Configuration for Development

Create `config/bot_config.json`:

```json
{
  "response": {
    "max_tokens": 500,
    "temperature": 0.9,
    "response_style": "conversational"
  },
  "access": {
    "allowed_numbers": ["+your-phone-number"],
    "whitelist_mode": false,
    "admin_numbers": ["+your-phone-number"]
  },
  "enabled": true,
  "maintenance_mode": false
}
```

### Development Environment Variables

For easier development, you can also set:

```bash
# In python-api/.env
DEBUG=true
AUTO_RELOAD=true
LOG_LEVEL=DEBUG
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

## 🛠️ Development Tools

### Code Formatting

```bash
# Install development tools
cd python-api
pip install black flake8 pytest

# Format code
black src/
flake8 src/

# Run tests
pytest
```

### Database Migrations

```bash
# If you modify database models
cd python-api
source venv/bin/activate

# Create migration
alembic revision --autogenerate -m "Description of changes"

# Apply migration
alembic upgrade head
```

### Hot Reload Setup

For automatic restarts during development:

```bash
# Install nodemon for Node.js
npm install -g nodemon

# Install uvicorn with reload for Python
pip install uvicorn[standard]

# Start with hot reload
cd python-api
uvicorn src.whatsapp_bot.main:app --reload --host 0.0.0.0 --port 8000

# Start Node.js with hot reload
cd node-bot
nodemon app.js
```

## 🐛 Troubleshooting

### Common Issues

**PostgreSQL connection failed:**
```bash
# Check if PostgreSQL is running
brew services list | grep postgresql  # macOS
sudo systemctl status postgresql      # Linux

# Reset password if needed
sudo -u postgres psql -c "ALTER USER chatbot_user PASSWORD 'dev_password';"
```

**Redis connection failed:**
```bash
# Check Redis status
redis-cli ping

# Restart Redis
brew services restart redis           # macOS
sudo systemctl restart redis-server  # Linux
```

**WhatsApp QR code not appearing:**
```bash
# Install Chrome dependencies (Linux)
sudo apt install -y libnss3 libatk-bridge2.0-0 libdrm2 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libxss1 libasound2

# Check Chrome installation
google-chrome --version
```

**OpenAI API errors:**
- Verify your API key is correct
- Check your OpenAI account has credits
- Ensure the API key has proper permissions

### Reset Development Environment

```bash
# Stop all services
pkill -f "python -m src.whatsapp_bot.main"
pkill -f "node app.js"

# Clear database
psql -U chatbot_user -d chatbot_db -h localhost -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

# Clear Redis
redis-cli FLUSHALL

# Restart services
cd python-api && source venv/bin/activate && python -m src.whatsapp_bot.main &
cd node-bot && node app.js &
```

## 📝 Development Notes

- **Database**: Use `dev_password` for local development (never in production)
- **API Keys**: Keep your OpenAI API key secure and never commit it to version control
- **WhatsApp**: The QR code expires after a few minutes, generate a new one if needed
- **Logs**: Check terminal outputs for debugging information
- **Rate Limits**: Development settings are more permissive than production

## 🔄 Daily Development Workflow

1. **Start development:**
   ```bash
   # Terminal 1: Python API
   cd python-api && source venv/bin/activate && python -m src.whatsapp_bot.main
   
   # Terminal 2: Node.js Bot
   cd node-bot && node app.js
   ```

2. **Test changes:**
   ```bash
   curl http://localhost:8000/health
   # Send test WhatsApp message
   ```

3. **Check logs and data:**
   ```bash
   # Database
   psql -U chatbot_user -d chatbot_db -h localhost
   
   # Redis
   redis-cli KEYS "*"
   ```

4. **Stop development:**
   ```bash
   # Ctrl+C in both terminals
   # Or kill processes
   pkill -f "python -m src.whatsapp_bot.main"
   pkill -f "node app.js"
   ```

---

**Ready to develop!** 🎉 Your local WhatsApp OpenAI Bot should now be running and ready for development. 