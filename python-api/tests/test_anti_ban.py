#!/usr/bin/env python3
"""
Test script for anti-ban functionality
"""

import asyncio
import time
import requests
import json
from datetime import datetime

# API base URL
BASE_URL = "http://localhost:8000"

def test_chat_endpoint(phone: str, message: str):
    """Test the chat endpoint with anti-ban measures"""
    url = f"{BASE_URL}/chat"
    payload = {
        "phone": phone,
        "message": message
    }
    
    start_time = time.time()
    response = requests.post(url, json=payload)
    end_time = time.time()
    
    response_time = end_time - start_time
    
    print(f"📱 Phone: {phone}")
    print(f"💬 Message: {message}")
    print(f"⏱️  Response time: {response_time:.2f}s")
    
    if response.status_code == 200:
        data = response.json()
        print(f"🤖 Response: {data.get('response', 'No response')}")
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")
    
    print("-" * 50)
    return response

def test_anti_ban_stats():
    """Test anti-ban statistics endpoint"""
    url = f"{BASE_URL}/anti-ban/stats"
    response = requests.get(url)
    
    print("📊 Anti-Ban Statistics:")
    if response.status_code == 200:
        stats = response.json()
        print(json.dumps(stats, indent=2))
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")
    
    print("-" * 50)

def test_health_checks():
    """Test health check endpoints"""
    endpoints = [
        "/health",
        "/health/redis", 
        "/health/anti-ban"
    ]
    
    print("🏥 Health Checks:")
    for endpoint in endpoints:
        url = f"{BASE_URL}{endpoint}"
        response = requests.get(url)
        status = "✅" if response.status_code == 200 else "❌"
        print(f"{status} {endpoint}: {response.status_code}")
    
    print("-" * 50)

def test_spam_detection():
    """Test spam detection functionality"""
    spam_messages = [
        "BUY NOW! Limited time offer!",
        "Click this link: http://spam.com http://more-spam.com http://even-more-spam.com",
        "FREE MONEY GUARANTEED NO RISK!!!",
        "URGENT ACT NOW LIMITED OFFER"
    ]
    
    print("🚫 Testing Spam Detection:")
    for message in spam_messages:
        print(f"Testing: {message}")
        response = test_chat_endpoint("+1234567890", message)
        time.sleep(1)  # Brief pause between tests

def test_opt_out():
    """Test opt-out functionality"""
    opt_out_messages = [
        "stop",
        "unsubscribe", 
        "opt out",
        "leave me alone"
    ]
    
    print("🛑 Testing Opt-Out Detection:")
    for message in opt_out_messages:
        print(f"Testing opt-out: {message}")
        response = test_chat_endpoint("+9999999999", message)
        time.sleep(1)

def test_rate_limiting():
    """Test rate limiting by sending multiple messages quickly"""
    print("⚡ Testing Rate Limiting:")
    phone = "+1111111111"
    
    for i in range(5):
        message = f"Test message {i+1}"
        print(f"Sending message {i+1}/5...")
        response = test_chat_endpoint(phone, message)
        # Don't add delay to test rate limiting
    
def test_new_user_limiting():
    """Test new user rate limiting"""
    print("👥 Testing New User Rate Limiting:")
    
    for i in range(12):  # Try to exceed the limit of 10 new users per hour
        phone = f"+555000{i:04d}"
        message = "Hello, I'm a new user!"
        print(f"New user {i+1}/12: {phone}")
        response = test_chat_endpoint(phone, message)
        time.sleep(0.5)  # Brief pause

def main():
    """Run all anti-ban tests"""
    print("🛡️  WhatsApp Bot Anti-Ban Testing")
    print("=" * 50)
    print(f"🕐 Test started at: {datetime.now()}")
    print("=" * 50)
    
    # Test health checks first
    test_health_checks()
    
    # Test anti-ban statistics
    test_anti_ban_stats()
    
    # Test normal conversation (should work)
    print("💬 Testing Normal Conversation:")
    test_chat_endpoint("+1234567890", "Hello, how are you?")
    time.sleep(2)
    test_chat_endpoint("+1234567890", "What's the weather like?")
    time.sleep(2)
    
    # Test spam detection
    test_spam_detection()
    
    # Test opt-out functionality
    test_opt_out()
    
    # Test rate limiting
    test_rate_limiting()
    
    # Test new user limiting
    test_new_user_limiting()
    
    # Final statistics
    print("📊 Final Anti-Ban Statistics:")
    test_anti_ban_stats()
    
    print("✅ Anti-ban testing completed!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️  Testing interrupted by user")
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}") 