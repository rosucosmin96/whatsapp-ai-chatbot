# 🤖 WhatsApp OpenAI Bot

A simple, production-ready WhatsApp chatbot powered by OpenAI GPT with conversation history and Redis caching.

## 🏗️ How It Works

```
WhatsApp Message → Node.js Bot → Python API → OpenAI GPT → Response
                                     ↓
                              PostgreSQL + Redis Cache
```

## 📁 Project Structure

```
whatsapp-openai-bot/
├── node-bot/              # WhatsApp Web automation
│   ├── app.js             # Main WhatsApp listener
│   ├── config.js          # API configuration
│   └── package.json       # Dependencies
├── python-api/            # FastAPI backend
│   ├── src/whatsapp_bot/  # Main application
│   ├── requirements.txt   # Python dependencies
│   └── .env               # Environment variables
└── README.md              # This file
```

## 🚀 VPS Installation Guide

### Step 1: Prepare Your VPS

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install essential packages
sudo apt install -y curl wget git vim tmux htop
```

### Step 2: Install Node.js

```bash
# Install Node.js 20.x
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Verify installation
node --version
npm --version
```

### Step 3: Install Python 3.11

```bash
# Install Python 3.11
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-pip

# Set Python 3.11 as default
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
```

### Step 4: Install PostgreSQL

```bash
# Install PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Start and enable PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql << EOF
CREATE DATABASE chatbot_db;
CREATE USER chatbot_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE chatbot_db TO chatbot_user;
\q
EOF
```

### Step 5: Install Redis

```bash
# Install Redis
sudo apt install -y redis-server

# Start and enable Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Test Redis
redis-cli ping
```

### Step 6: Install Chrome Dependencies (for WhatsApp Web)

```bash
# Install Chrome dependencies
sudo apt install -y \
  libnss3 \
  libnspr4 \
  libatk-bridge2.0-0 \
  libdrm2 \
  libxkbcomposite1 \
  libxdamage1 \
  libxrandr2 \
  libgbm1 \
  libxss1 \
  libasound2 \
  libatspi2.0-0 \
  libgtk-3-0
```

## 📦 Application Setup

### Step 1: Clone Repository

```bash
# Clone the repository
git clone <your-repository-url>
cd whatsapp-openai-bot
```

### Step 2: Setup Python API

```bash
# Navigate to Python API directory
cd python-api

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Configure Environment

```bash
# Create environment file
cat > .env << EOF
# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-3.5-turbo

# Database Configuration
DATABASE_URL=postgresql://chatbot_user:your_secure_password@localhost:5432/chatbot_db

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Application Configuration
PROMPTS_DIR=prompts
LOG_LEVEL=INFO

# Anti-Ban Configuration
MAX_NEW_USERS_PER_HOUR=10
MIN_REPLY_DELAY=2.0
MAX_REPLY_DELAY=5.0
GLOBAL_RATE_LIMIT=1.0
EOF
```

### Step 4: Setup Node.js Bot

```bash
# Navigate to Node.js bot directory
cd ../node-bot

# Install dependencies
npm install
```

## 🖥️ Running with tmux

### Start Services Using tmux

```bash
# Create a new tmux session
tmux new-session -d -s whatsapp-bot

# Split into 2 panes
tmux split-window -h

# Pane 0: Python API
tmux send-keys -t whatsapp-bot:0 'cd python-api && source venv/bin/activate && python -m src.whatsapp_bot.main' Enter

# Pane 1: Node.js Bot
tmux send-keys -t whatsapp-bot:1 'cd node-bot && node app.js' Enter

# Attach to session to view logs
tmux attach-session -t whatsapp-bot
```

### tmux Commands

```bash
# Attach to existing session
tmux attach-session -t whatsapp-bot

# Detach from session (keep running)
Ctrl+B, then D

# List sessions
tmux list-sessions

# Kill session
tmux kill-session -t whatsapp-bot

# Switch between panes
Ctrl+B, then arrow keys

# Create new window
Ctrl+B, then C

# Switch between windows
Ctrl+B, then 0-9
```

## 📱 WhatsApp Setup

1. **Start the application** using tmux (see above)
2. **Scan QR code** - The Node.js bot will display a QR code in the terminal
3. **Scan with WhatsApp** - Open WhatsApp on your phone and scan the QR code
4. **Test the bot** - Send a message to your WhatsApp number

## 🧪 Testing

### Health Check

```bash
# Check if API is running
curl http://localhost:8000/health

# Check Redis connection
curl http://localhost:8000/health/redis
```

### Send Test Message

```bash
# Send a test message
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+1234567890",
    "message": "Hello, how are you?"
  }'
```

### View API Documentation

```bash
# Open API docs in browser
curl http://localhost:8000/docs
```

## ⚙️ Configuration

### Bot Configuration

Create `config/bot_config.json`:

```json
{
  "response": {
    "max_tokens": 1000,
    "temperature": 0.8,
    "response_style": "conversational"
  },
  "access": {
    "allowed_numbers": ["+1234567890"],
    "whitelist_mode": false,
    "admin_numbers": ["+1234567890"]
  },
  "enabled": true,
  "maintenance_mode": false
}
```

### Admin Commands (via WhatsApp)

```
/help                    - Show available commands
/config                  - Show current configuration
/config enable/disable   - Enable/disable bot
/allow +1234567890      - Allow a phone number
/block +1234567890      - Block a phone number
```

## 🛡️ Security & Anti-Ban

The bot includes several safety features:

- **Rate limiting** - Prevents spam and reduces ban risk
- **Human-like delays** - Random response delays (2-5 seconds)
- **Conversation limits** - Daily message limits with gradual warm-up
- **User opt-out** - Automatic handling of "stop" messages

## 📊 Monitoring

### View Logs

```bash
# Attach to tmux session to see live logs
tmux attach-session -t whatsapp-bot

# View Python API logs (pane 0)
Ctrl+B, then 0

# View Node.js bot logs (pane 1)
Ctrl+B, then 1
```

### Database Monitoring

```bash
# Connect to database
sudo -u postgres psql -d chatbot_db

# View recent conversations
SELECT * FROM chat_interactions ORDER BY created_at DESC LIMIT 10;

# View users
SELECT * FROM users;
```

### Redis Monitoring

```bash
# Check Redis keys
redis-cli KEYS "*"

# View conversation cache
redis-cli LRANGE "user:1:conversations" 0 -1
```

## 🔧 Maintenance

### Restart Services

```bash
# Kill existing session
tmux kill-session -t whatsapp-bot

# Start services again
tmux new-session -d -s whatsapp-bot
tmux split-window -h
tmux send-keys -t whatsapp-bot:0 'cd python-api && source venv/bin/activate && python -m src.whatsapp_bot.main' Enter
tmux send-keys -t whatsapp-bot:1 'cd node-bot && node app.js' Enter
```

### Update Application

```bash
# Pull latest changes
git pull origin main

# Update Python dependencies
cd python-api
source venv/bin/activate
pip install -r requirements.txt

# Update Node.js dependencies
cd ../node-bot
npm install

# Restart services (see above)
```

## 💾 Database Backup & Restoration

### Create Database Backup

```bash
# Create a backup of the entire database
sudo -u postgres pg_dump chatbot_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Create a compressed backup
sudo -u postgres pg_dump chatbot_db | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz

# Create a custom format backup (recommended for large databases)
sudo -u postgres pg_dump -Fc chatbot_db > backup_$(date +%Y%m%d_%H%M%S).dump

# Backup with specific tables only
sudo -u postgres pg_dump -t users -t chat_interactions chatbot_db > backup_tables_$(date +%Y%m%d_%H%M%S).sql
```

### Restore Database from Backup

#### Method 1: Restore SQL Dump File

```bash
# Stop the applications first
tmux kill-session -t whatsapp-bot

# Drop existing database (WARNING: This deletes all current data)
sudo -u postgres dropdb chatbot_db

# Create new empty database
sudo -u postgres createdb chatbot_db

sudo -u postgres psql -c "CREATE USER chatbot_user WITH PASSWORD 'your_secure_password';"

# Grant permissions to user
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE chatbot_db TO chatbot_user;"

# Restore from SQL backup file
sudo -u postgres psql chatbot_db < backup_20241201_143000.sql

# If backup is compressed
gunzip -c backup_20241201_143000.sql.gz | sudo -u postgres psql chatbot_db
```

#### Method 2: Restore Custom Format Backup

```bash
# Stop applications
tmux kill-session -t whatsapp-bot

# Drop and recreate database
sudo -u postgres dropdb chatbot_db
sudo -u postgres createdb chatbot_db
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE chatbot_db TO chatbot_user;"

# Restore from custom format backup
sudo -u postgres pg_restore -d chatbot_db backup_20241201_143000.dump

# Restore with verbose output
sudo -u postgres pg_restore -v -d chatbot_db backup_20241201_143000.dump
```

#### Method 3: Restore Without Dropping Database (Data Only)

```bash
# Restore only data (tables must exist)
sudo -u postgres pg_restore --data-only -d chatbot_db backup_20241201_143000.dump

# Restore specific tables only
sudo -u postgres pg_restore -t users -t chat_interactions -d chatbot_db backup_20241201_143000.dump
```

### Start Fresh Database with Backup

If you want to set up PostgreSQL from scratch with a backup file:

```bash
# Install PostgreSQL (if not already installed)
sudo apt install -y postgresql postgresql-contrib

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create user and database
sudo -u postgres psql << EOF
CREATE USER chatbot_user WITH PASSWORD 'your_secure_password';
CREATE DATABASE chatbot_db OWNER chatbot_user;
GRANT ALL PRIVILEGES ON DATABASE chatbot_db TO chatbot_user;
\q
EOF

# Restore from backup
sudo -u postgres psql chatbot_db < your_backup_file.sql

# Verify restoration
sudo -u postgres psql -d chatbot_db -c "SELECT COUNT(*) FROM users;"
sudo -u postgres psql -d chatbot_db -c "SELECT COUNT(*) FROM chat_interactions;"
```

### Verify Backup Integrity

```bash
# Test if backup file is valid
sudo -u postgres pg_restore --list backup_20241201_143000.dump

# Test SQL backup file
head -20 backup_20241201_143000.sql

# Check backup file size
ls -lh backup_*.sql*

# Verify backup can be restored to test database
sudo -u postgres createdb test_restore
sudo -u postgres psql test_restore < backup_20241201_143000.sql
sudo -u postgres psql -d test_restore -c "\dt"  # List tables
sudo -u postgres dropdb test_restore  # Clean up
```

### Migration Between Servers

```bash
# On source server - create backup
sudo -u postgres pg_dump -Fc chatbot_db > chatbot_backup.dump

# Transfer to new server
scp chatbot_backup.dump user@new-server:/home/user/

# On new server - restore
sudo -u postgres createdb chatbot_db
sudo -u postgres psql -c "CREATE USER chatbot_user WITH PASSWORD 'your_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE chatbot_db TO chatbot_user;"
sudo -u postgres pg_restore -d chatbot_db chatbot_backup.dump
```

## 🆘 Troubleshooting

### Common Issues

1. **QR Code not appearing** - Check if Chrome dependencies are installed
2. **Database connection errors** - Verify PostgreSQL is running and credentials are correct
3. **Redis connection errors** - Check if Redis is running
4. **OpenAI API errors** - Verify API key is correct and has credits

### Logs Location

- Python API logs: Terminal pane 0 in tmux session
- Node.js bot logs: Terminal pane 1 in tmux session
- System logs: `/var/log/` (for services)

### Reset Everything

```bash
# Stop all services
tmux kill-session -t whatsapp-bot

# Reset database
sudo -u postgres dropdb chatbot_db
sudo -u postgres createdb chatbot_db

# Clear Redis cache
redis-cli FLUSHALL

# Restart services
# (follow tmux setup steps above)
```

## 📞 Support

If you encounter issues:

1. Check the logs in your tmux session
2. Verify all services are running: `sudo systemctl status postgresql redis-server`
3. Test API endpoints manually with curl
4. Check your OpenAI API key and credits

---

**Note**: This bot requires an active WhatsApp account and OpenAI API credits. Make sure to follow WhatsApp's terms of service and use responsibly.