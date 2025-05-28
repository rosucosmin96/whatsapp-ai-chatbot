#!/usr/bin/env python3
"""
Test script for configuration management functionality
"""

import requests
import json
import time
from datetime import datetime

# API base URL
BASE_URL = "http://localhost:8000"

def test_config_endpoints():
    """Test configuration management endpoints"""
    print("🔧 Testing Configuration Management")
    print("=" * 50)
    
    # Test getting current config
    print("📋 Getting current configuration...")
    response = requests.get(f"{BASE_URL}/config")
    if response.status_code == 200:
        config = response.json()
        print("✅ Current configuration:")
        print(json.dumps(config, indent=2))
    else:
        print(f"❌ Error getting config: {response.status_code}")
    
    print("-" * 50)
    
    # Test config summary
    print("📊 Getting configuration summary...")
    response = requests.get(f"{BASE_URL}/config/summary")
    if response.status_code == 200:
        summary = response.json()
        print("✅ Configuration summary:")
        for key, value in summary.items():
            print(f"  • {key}: {value}")
    else:
        print(f"❌ Error getting summary: {response.status_code}")
    
    print("-" * 50)

def test_response_config():
    """Test response configuration updates"""
    print("📝 Testing Response Configuration")
    print("=" * 30)
    
    # Test updating response length
    print("🔧 Setting response length to 500 tokens...")
    response = requests.put(f"{BASE_URL}/config/response", json={
        "max_tokens": 500,
        "response_style": "brief"
    })
    if response.status_code == 200:
        print("✅ Response configuration updated")
        print(f"Response: {response.json()}")
    else:
        print(f"❌ Error updating response config: {response.status_code}")
    
    # Test invalid values
    print("🚫 Testing invalid token count...")
    response = requests.put(f"{BASE_URL}/config/response", json={
        "max_tokens": 5000  # Too high
    })
    if response.status_code == 400:
        print("✅ Validation working - rejected invalid token count")
    else:
        print(f"❌ Validation failed: {response.status_code}")
    
    print("-" * 30)

def test_access_control():
    """Test access control features"""
    print("🔐 Testing Access Control")
    print("=" * 30)
    
    test_phone = "+1234567890"
    
    # Add to allowed numbers
    print(f"➕ Adding {test_phone} to allowed numbers...")
    response = requests.post(f"{BASE_URL}/config/numbers/allow/{test_phone}")
    if response.status_code == 200:
        print("✅ Number added to allowed list")
    else:
        print(f"❌ Error adding number: {response.status_code}")
    
    # Check number access
    print(f"🔍 Checking access for {test_phone}...")
    response = requests.get(f"{BASE_URL}/config/numbers/check/{test_phone}")
    if response.status_code == 200:
        access_info = response.json()
        print("✅ Access check result:")
        for key, value in access_info.items():
            print(f"  • {key}: {value}")
    else:
        print(f"❌ Error checking access: {response.status_code}")
    
    # Test whitelist mode
    print("🔒 Enabling whitelist mode...")
    response = requests.put(f"{BASE_URL}/config/access", json={
        "whitelist_mode": True
    })
    if response.status_code == 200:
        print("✅ Whitelist mode enabled")
    else:
        print(f"❌ Error enabling whitelist: {response.status_code}")
    
    print("-" * 30)

def test_maintenance_mode():
    """Test maintenance mode functionality"""
    print("🔧 Testing Maintenance Mode")
    print("=" * 30)
    
    # Enable maintenance mode
    print("🚧 Enabling maintenance mode...")
    response = requests.post(f"{BASE_URL}/config/maintenance", params={
        "enabled": True,
        "message": "Bot is under maintenance for testing"
    })
    if response.status_code == 200:
        print("✅ Maintenance mode enabled")
        print(f"Response: {response.json()}")
    else:
        print(f"❌ Error enabling maintenance: {response.status_code}")
    
    # Test chat during maintenance
    print("💬 Testing chat during maintenance...")
    response = requests.post(f"{BASE_URL}/chat", json={
        "phone": "+1234567890",
        "message": "Hello during maintenance"
    })
    if response.status_code == 200:
        chat_response = response.json()
        print(f"✅ Maintenance response: {chat_response['response']}")
    else:
        print(f"❌ Error during maintenance chat: {response.status_code}")
    
    # Disable maintenance mode
    print("✅ Disabling maintenance mode...")
    response = requests.post(f"{BASE_URL}/config/maintenance", params={
        "enabled": False
    })
    if response.status_code == 200:
        print("✅ Maintenance mode disabled")
    else:
        print(f"❌ Error disabling maintenance: {response.status_code}")
    
    print("-" * 30)

def test_admin_numbers():
    """Test admin number management"""
    print("👑 Testing Admin Number Management")
    print("=" * 30)
    
    test_admin_phone = "+9876543210"
    existing_admin = "+1234567890"  # Should already be admin
    
    # Test adding admin number via API
    print(f"➕ Adding {test_admin_phone} to admin numbers via API...")
    response = requests.post(f"{BASE_URL}/config/numbers/admin/{test_admin_phone}")
    if response.status_code == 200:
        print("✅ Admin number added via API")
        print(f"Response: {response.json()}")
    else:
        print(f"❌ Error adding admin number: {response.status_code}")
    
    # Check admin status
    print(f"🔍 Checking admin status for {test_admin_phone}...")
    response = requests.get(f"{BASE_URL}/config/numbers/check/{test_admin_phone}")
    if response.status_code == 200:
        access_info = response.json()
        print("✅ Admin check result:")
        for key, value in access_info.items():
            print(f"  • {key}: {value}")
    else:
        print(f"❌ Error checking admin status: {response.status_code}")
    
    # Test admin command via chat (using existing admin)
    print(f"👑 Testing /admin command via chat...")
    response = requests.post(f"{BASE_URL}/chat", json={
        "phone": existing_admin,
        "message": f"/admin +5555555555"
    })
    if response.status_code == 200:
        admin_response = response.json()
        print(f"✅ Admin command response: {admin_response['response']}")
    else:
        print(f"❌ Error with admin command: {response.status_code}")
    
    # Test unadmin command via chat
    print(f"👤 Testing /unadmin command via chat...")
    response = requests.post(f"{BASE_URL}/chat", json={
        "phone": existing_admin,
        "message": f"/unadmin +5555555555"
    })
    if response.status_code == 200:
        unadmin_response = response.json()
        print(f"✅ Unadmin command response: {unadmin_response['response']}")
    else:
        print(f"❌ Error with unadmin command: {response.status_code}")
    
    # Remove admin number via API
    print(f"➖ Removing {test_admin_phone} from admin numbers via API...")
    response = requests.delete(f"{BASE_URL}/config/numbers/admin/{test_admin_phone}")
    if response.status_code == 200:
        print("✅ Admin number removed via API")
        print(f"Response: {response.json()}")
    else:
        print(f"❌ Error removing admin number: {response.status_code}")
    
    print("-" * 30)

def test_admin_commands():
    """Test admin commands via chat"""
    print("👑 Testing Admin Commands")
    print("=" * 30)
    
    admin_phone = "+1234567890"  # This should be in admin_numbers in config
    
    # Test help command
    print("❓ Testing /help command...")
    response = requests.post(f"{BASE_URL}/chat", json={
        "phone": admin_phone,
        "message": "/help"
    })
    if response.status_code == 200:
        help_response = response.json()
        print("✅ Help command response:")
        print(help_response['response'])
    else:
        print(f"❌ Error with help command: {response.status_code}")
    
    # Test config command
    print("⚙️ Testing /config command...")
    response = requests.post(f"{BASE_URL}/chat", json={
        "phone": admin_phone,
        "message": "/config"
    })
    if response.status_code == 200:
        config_response = response.json()
        print("✅ Config command response:")
        print(config_response['response'])
    else:
        print(f"❌ Error with config command: {response.status_code}")
    
    # Test token setting
    print("📝 Testing /config tokens command...")
    response = requests.post(f"{BASE_URL}/chat", json={
        "phone": admin_phone,
        "message": "/config tokens 800"
    })
    if response.status_code == 200:
        token_response = response.json()
        print(f"✅ Token setting response: {token_response['response']}")
    else:
        print(f"❌ Error with token command: {response.status_code}")
    
    print("-" * 30)

def test_response_styles():
    """Test different response styles"""
    print("🎨 Testing Response Styles")
    print("=" * 30)
    
    test_phone = "+1234567890"
    test_message = "Explain how artificial intelligence works"
    
    styles = ["brief", "conversational", "detailed"]
    
    for style in styles:
        print(f"🔧 Setting style to {style}...")
        
        # Update style
        requests.put(f"{BASE_URL}/config/response", json={
            "response_style": style
        })
        
        # Test response
        print(f"💬 Testing {style} response...")
        response = requests.post(f"{BASE_URL}/chat", json={
            "phone": test_phone,
            "message": test_message
        })
        
        if response.status_code == 200:
            chat_response = response.json()
            print(f"✅ {style.title()} response ({len(chat_response['response'])} chars):")
            print(f"   {chat_response['response'][:100]}...")
        else:
            print(f"❌ Error with {style} style: {response.status_code}")
        
        time.sleep(2)  # Respect rate limits
    
    print("-" * 30)

def main():
    """Run all configuration tests"""
    print("🔧 WhatsApp Bot Configuration Testing")
    print("=" * 50)
    print(f"🕐 Test started at: {datetime.now()}")
    print("=" * 50)
    
    try:
        # Test basic config endpoints
        test_config_endpoints()
        
        # Test response configuration
        test_response_config()
        
        # Test access control
        test_access_control()
        
        # Test maintenance mode
        test_maintenance_mode()
        
        # Test admin numbers
        test_admin_numbers()
        
        # Test admin commands
        test_admin_commands()
        
        # Test response styles
        test_response_styles()
        
        print("✅ All configuration tests completed!")
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
    
    finally:
        # Reset to defaults
        print("🔄 Resetting to default configuration...")
        requests.put(f"{BASE_URL}/config/response", json={
            "max_tokens": 1000,
            "response_style": "conversational",
            "temperature": 0.8
        })
        requests.put(f"{BASE_URL}/config/access", json={
            "whitelist_mode": False
        })
        requests.post(f"{BASE_URL}/config/maintenance", params={
            "enabled": False
        })
        print("✅ Configuration reset to defaults")

if __name__ == "__main__":
    main() 