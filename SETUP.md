# 🛠️ WhatsApp OpenAI Bot - Complete Setup Guide

This comprehensive guide will walk you through setting up the WhatsApp OpenAI Bot from scratch, including all dependencies, database configuration, and testing procedures.

## 📋 Prerequisites

Before starting, ensure you have the following:

### System Requirements
- **Operating System**: macOS, Linux, or Windows
- **Python**: 3.10 or higher (Required)
- **Node.js**: 18.0 or higher
- **Git**: For cloning the repository
- **OpenAI API Key**: From [OpenAI Platform](https://platform.openai.com/)

### Hardware Requirements
- **RAM**: Minimum 4GB (8GB recommended)
- **Storage**: At least 2GB free space
- **Network**: Stable internet connection

---

## 🚀 Step-by-Step Installation

### Step 1: Install System Dependencies

#### macOS (using Homebrew)
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install required packages
brew install python@3.11 node postgresql redis git
brew install --cask google-chrome  # For WhatsApp Web automation

# Start services
brew services start postgresql
brew services start redis
```

#### Ubuntu/Debian Linux
```bash
# Update package list
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Install PostgreSQL and Redis
sudo apt install -y postgresql postgresql-contrib redis-server

# Install Chrome for WhatsApp automation
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
sudo apt update
sudo apt install -y google-chrome-stable

# Start services
sudo systemctl start postgresql
sudo systemctl start redis-server
sudo systemctl enable postgresql
sudo systemctl enable redis-server
```

#### Windows
```powershell
# Install using Chocolatey (run as Administrator)
# First install Chocolatey: https://chocolatey.org/install

choco install python311 nodejs postgresql redis-64 git googlechrome -y

# Start PostgreSQL service
net start postgresql-x64-14

# Start Redis service
net start redis
```

### Step 2: Clone and Setup Project

```bash
# Clone the repository
git clone <your-repository-url>
cd whatsapp-openai-bot

# Verify Python version
python3 --version  # Should be 3.10+
```

### Step 3: Setup Python Backend

```bash
# Navigate to Python API directory
cd python-api

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Verify installation
pip list
```

### Step 4: Configure PostgreSQL Database

#### Option A: Automated Setup (Recommended)
```bash
# Run the database setup script
python -c "
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Connect to PostgreSQL
conn = psycopg2.connect(
    host='localhost',
    user='postgres',
    password='',  # Default empty password on macOS/Linux
    database='postgres'
)
conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
cur = conn.cursor()

# Create database and user
try:
    cur.execute('CREATE DATABASE chatbot_db;')
    print('Database created successfully')
except psycopg2.errors.DuplicateDatabase:
    print('Database already exists')

try:
    cur.execute(\"CREATE USER chatbot_user WITH PASSWORD 'your_secure_password';\")
    print('User created successfully')
except psycopg2.errors.DuplicateObject:
    print('User already exists')

cur.execute('GRANT ALL PRIVILEGES ON DATABASE chatbot_db TO chatbot_user;')
print('Privileges granted')

cur.close()
conn.close()
print('Database setup completed!')
"
```

#### Option B: Manual Setup
```bash
# Connect to PostgreSQL
psql postgres

# In PostgreSQL prompt:
CREATE DATABASE chatbot_db;
CREATE USER chatbot_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE chatbot_db TO chatbot_user;
\q
```

### Step 5: Configure Redis

```bash
# Test Redis connection
redis-cli ping
# Should return: PONG

# Check Redis configuration
redis-cli info server
```

### Step 6: Environment Configuration

#### Create Python API .env file
```bash
# Create .env file in python-api directory
cd python-api
cat > .env << 'EOF'
# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-api-key-here

# Database Configuration
DATABASE_URL=postgresql://chatbot_user:your_secure_password@localhost:5432/chatbot_db

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# Application Configuration
PROMPTS_DIR=prompts
LOG_LEVEL=INFO

# Backup Configuration
BACKUP_RETENTION_HOURS=2
BACKUP_SCHEDULE_HOURS=1
EOF
```

#### Create Node.js Bot .env file
```bash
# Create .env file in node-bot directory
cd ../node-bot
cat > .env << 'EOF'
# API Configuration
API_URL=http://localhost:8000/chat

# WhatsApp Configuration
WHATSAPP_SESSION_PATH=./session
EOF
```

### Step 7: Install Node.js Dependencies

```bash
# In node-bot directory
npm install

# Verify installation
npm list
```

---

## 🔧 Database Initialization

### Initialize Database Tables
```bash
# Navigate to Python API directory
cd python-api
source venv/bin/activate  # Activate virtual environment

# Initialize database schema
python -c "
from src.whatsapp_bot.database import init_db
init_db()
print('Database tables created successfully!')
"
```

### Verify Database Setup
```bash
# Connect to database and verify tables
psql -U chatbot_user -d chatbot_db

# In PostgreSQL prompt:
\dt  # List tables
SELECT * FROM users LIMIT 5;
SELECT * FROM chat_interactions LIMIT 5;
\q
```

---

## 🚀 Starting the Application

### Terminal 1: Start Python API
```bash
cd python-api
source venv/bin/activate
python -m src.whatsapp_bot.main
```

You should see:
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Terminal 2: Start WhatsApp Bot
```bash
cd node-bot
node app.js
```

You should see a QR code displayed in the terminal.

### Terminal 3: Start Backup Service (Optional)
```bash
cd python-api
source venv/bin/activate
python -m src.whatsapp_bot.services.backup_service schedule
```

---

## 📱 WhatsApp Connection

1. **Scan QR Code**: Use your WhatsApp mobile app to scan the QR code
2. **Wait for Connection**: You should see "WhatsApp client is ready!"
3. **Test Connection**: Send a message to your WhatsApp number from another device

---

## 🧪 Comprehensive Testing

### 1. API Health Checks

```bash
# Test general health
curl http://localhost:8000/health
# Expected: {"status": "ok"}

# Test Redis health
curl http://localhost:8000/health/redis
# Expected: {"status": "ok", "cache_ttl_minutes": 30}

# Test API documentation
open http://localhost:8000/docs  # Opens Swagger UI
```

### 2. Database Testing

```bash
# Test database connection
python -c "
from src.whatsapp_bot.database import get_db
from sqlalchemy.orm import Session

db = next(get_db())
result = db.execute('SELECT 1 as test').fetchone()
print(f'Database test result: {result.test}')
db.close()
"
```

### 3. Redis Testing

```bash
# Test Redis connection
redis-cli ping

# Test Redis operations
redis-cli set test_key "test_value"
redis-cli get test_key
redis-cli del test_key

# Check Redis info
redis-cli info memory
```

### 4. Chat API Testing

```bash
# Test chat endpoint
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+1234567890",
    "message": "Hello, this is a test message!"
  }'

# Expected response:
# {"response": "Hello! How can I help you today?"}
```

### 5. Conversation History Testing

```bash
# Get conversation history
curl "http://localhost:8000/history/+1234567890?limit=5"

# Expected: Array of conversation objects
```

### 6. Redis Cache Inspection

```bash
# List all Redis keys
redis-cli KEYS "*"

# View user conversations (replace 1 with actual user ID)
redis-cli LRANGE "user:1:conversations" 0 -1

# Check TTL for cached data
redis-cli TTL "user:1:conversations"
```

### 7. Database Content Verification

```bash
# Connect to database
psql -U chatbot_user -d chatbot_db

# Check users table
SELECT id, phone, created_at FROM users ORDER BY created_at DESC LIMIT 5;

# Check interactions table
SELECT 
    u.phone, 
    ci.request_message, 
    ci.response_message, 
    ci.language,
    ci.created_at 
FROM chat_interactions ci 
JOIN users u ON ci.user_id = u.id 
ORDER BY ci.created_at DESC 
LIMIT 5;

# Check table sizes
SELECT 
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats 
WHERE schemaname = 'public';
```

---

## 🔄 Automated Backup Testing

### Test Manual Backup
```bash
# Create a manual backup
python -m src.whatsapp_bot.services.backup_service backup

# List available backups
python -m src.whatsapp_bot.services.backup_service list

# Test database connection
python -m src.whatsapp_bot.services.backup_service test
```

### Test Backup Restoration
```bash
# Create test data
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"phone": "+test123", "message": "Test before backup"}'

# Create backup
python -m src.whatsapp_bot.services.backup_service backup

# Simulate data loss (be careful!)
psql -U chatbot_user -d chatbot_db -c "TRUNCATE chat_interactions, users CASCADE;"

# Restore from backup
python -m src.whatsapp_bot.services.backup_service restore backups/backup_YYYY-MM-DD_HH-MM-SS.sql

# Verify restoration
psql -U chatbot_user -d chatbot_db -c "SELECT COUNT(*) FROM users; SELECT COUNT(*) FROM chat_interactions;"
```

---

## 🚨 Troubleshooting

### Common Issues and Solutions

#### 1. Python Version Issues
```bash
# Check Python version
python3 --version

# If version is < 3.10, install newer version
# On macOS:
brew install python@3.11
# On Ubuntu:
sudo apt install python3.11
```

#### 2. Database Connection Issues
```bash
# Check PostgreSQL status
# macOS:
brew services list | grep postgresql
# Linux:
sudo systemctl status postgresql

# Test connection manually
psql -U chatbot_user -d chatbot_db -c "SELECT 1;"
```

#### 3. Redis Connection Issues
```bash
# Check Redis status
# macOS:
brew services list | grep redis
# Linux:
sudo systemctl status redis

# Test Redis connection
redis-cli ping
```

#### 4. OpenAI API Issues
```bash
# Test API key
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models
```

#### 5. WhatsApp Connection Issues
```bash
# Clear WhatsApp session
rm -rf node-bot/session/

# Restart bot
cd node-bot
node app.js
```

---

## 📊 Monitoring and Maintenance

### Daily Checks
```bash
# Check service status
curl http://localhost:8000/health
redis-cli ping
psql -U chatbot_user -d chatbot_db -c "SELECT 1;"

# Check backup status
ls -la python-api/backups/
```

### Weekly Maintenance
```bash
# Update dependencies
cd python-api
pip list --outdated

cd ../node-bot
npm outdated

# Clean old logs
find . -name "*.log" -mtime +7 -delete

# Vacuum database
psql -U chatbot_user -d chatbot_db -c "VACUUM ANALYZE;"
```

---

## 📞 Support

If you encounter issues:

1. **Check Logs**: Review application and system logs
2. **Verify Configuration**: Double-check .env files
3. **Test Components**: Use the testing procedures above
4. **Create Issue**: Submit detailed bug report with logs 