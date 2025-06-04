#!/usr/bin/env python3
"""
Test script for anti-ban enable/disable functionality
"""

import requests
import time
import json

# API base URL
BASE_URL = "http://localhost:8000"

def send_admin_command(phone: str, command: str):
    """Send an admin command"""
    url = f"{BASE_URL}/chat"
    payload = {
        "phone": phone,
        "message": command
    }
    
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print(f"🤖 Response: {data.get('response', 'No response')}")
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")
    
    return response

def test_chat_message(phone: str, message: str):
    """Send a regular chat message and measure response time"""
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
    return response, response_time

def get_anti_ban_stats():
    """Get current anti-ban statistics"""
    url = f"{BASE_URL}/anti-ban/stats"
    
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        print("📊 Anti-Ban Statistics:")
        print(json.dumps(data, indent=2))
    else:
        print(f"❌ Error getting stats: {response.status_code} - {response.text}")

def main():
    """Test anti-ban enable/disable functionality"""
    print("🛡️  Anti-Ban Toggle Testing")
    print("=" * 50)
    
    admin_phone = "+1234567890"  # Assuming this is an admin number
    test_phone = "+9876543210"
    
    print("📊 Current Configuration:")
    send_admin_command(admin_phone, "/config")
    print()
    
    print("🛡️ Current Anti-Ban Status:")
    send_admin_command(admin_phone, "/config antiban")
    print()
    
    print("1️⃣ Testing with Anti-Ban ENABLED:")
    send_admin_command(admin_phone, "/config antiban on")
    
    # Test response times with anti-ban enabled
    print("\nTesting response times with anti-ban enabled:")
    times_enabled = []
    for i in range(3):
        _, response_time = test_chat_message(test_phone, f"Test message {i+1} with anti-ban enabled")
        times_enabled.append(response_time)
        time.sleep(1)
    
    avg_time_enabled = sum(times_enabled) / len(times_enabled)
    print(f"Average response time with anti-ban enabled: {avg_time_enabled:.2f}s")
    print()
    
    print("2️⃣ Testing with Anti-Ban DISABLED:")
    send_admin_command(admin_phone, "/config antiban off")
    
    # Test response times with anti-ban disabled
    print("\nTesting response times with anti-ban disabled:")
    times_disabled = []
    for i in range(3):
        _, response_time = test_chat_message(test_phone, f"Test message {i+1} with anti-ban disabled")
        times_disabled.append(response_time)
        time.sleep(0.5)  # Shorter delay since anti-ban is disabled
    
    avg_time_disabled = sum(times_disabled) / len(times_disabled)
    print(f"Average response time with anti-ban disabled: {avg_time_disabled:.2f}s")
    print()
    
    print("📈 Comparison:")
    print(f"Average response time (anti-ban enabled):  {avg_time_enabled:.2f}s")
    print(f"Average response time (anti-ban disabled): {avg_time_disabled:.2f}s")
    print(f"Time difference: {abs(avg_time_enabled - avg_time_disabled):.2f}s")
    print()
    
    print("3️⃣ Testing Spam Detection:")
    print("With anti-ban enabled:")
    send_admin_command(admin_phone, "/config antiban on")
    test_chat_message(test_phone, "BUY NOW! Limited time offer! Click this link!")
    
    print("With anti-ban disabled:")
    send_admin_command(admin_phone, "/config antiban off")
    test_chat_message(test_phone, "BUY NOW! Limited time offer! Click this link!")
    
    print("4️⃣ Final Statistics:")
    get_anti_ban_stats()
    
    print("✅ Anti-ban toggle testing completed!")

if __name__ == "__main__":
    main() 