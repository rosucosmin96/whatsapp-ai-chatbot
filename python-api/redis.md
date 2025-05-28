# Redis Integration for WhatsApp OpenAI Bot

This project now uses Redis for caching conversation history, which improves performance and reduces database load.

## Configuration

Add the following configuration to your `.env` file:

```
# Redis configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
```

## Installation

### macOS

```bash
# Using Homebrew
brew install redis
brew services start redis
```

### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

### Windows

Download and install from: https://github.com/microsoftarchive/redis/releases

## Testing Redis Connection

You can test the Redis connection using the health check endpoint:

```
GET /health/redis
```

Example response:
```json
{
  "status": "ok",
  "cache_ttl_minutes": 30
}
```

## Cache Details

- Conversation history is cached for 30 minutes
- Cache is automatically refreshed on new interactions
- If Redis is unavailable, the system will fall back to the database 