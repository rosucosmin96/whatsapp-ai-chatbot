#!/usr/bin/env python3
"""
Test script for language detection functionality
"""

import os
import sys
from pathlib import Path

# Add the src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from whatsapp_bot.services.language_service import LanguageDetectionService
from whatsapp_bot.config import config_manager

def test_language_detection():
    """Test the language detection service"""
    print("🧪 Testing Language Detection Service")
    print("=" * 50)
    
    # Initialize the language service
    language_service = LanguageDetectionService()
    
    # Test messages in different languages
    test_messages = [
        ("Hello, how are you doing today?", "english"),
        ("Salut, cum te mai duci?", "romanian"),
        ("Hola, ¿cómo estás hoy?", "spanish"),
        ("Bonjour, comment allez-vous?", "french"),
        ("Guten Tag, wie geht es Ihnen?", "german"),
        ("Hi", "english"),  # Short message test
        ("👋", "english"),  # Emoji test
    ]
    
    # Show current configuration
    lang_config = config_manager.get_language_config()
    print(f"Language Detection Enabled: {lang_config.detection_enabled}")
    print(f"Default Language: {lang_config.default_language}")
    print()
    
    # Test each message
    for message, expected_lang in test_messages:
        print(f"Testing: '{message}'")
        detected_lang = language_service.get_language_for_conversation(message)
        status = "✅" if detected_lang == expected_lang else "❌"
        print(f"  Expected: {expected_lang}")
        print(f"  Detected: {detected_lang} {status}")
        print()
    
    # Test with language detection disabled
    print("Testing with language detection disabled...")
    config_manager.update_language_config(detection_enabled=False)
    
    test_message = "Salut, cum te mai duci?"
    detected_lang = language_service.get_language_for_conversation(test_message)
    expected_default = config_manager.get_language_config().default_language
    
    print(f"Message: '{test_message}'")
    print(f"Detected (with detection disabled): {detected_lang}")
    print(f"Expected (default): {expected_default}")
    
    if detected_lang == expected_default:
        print("✅ Language detection disable functionality works!")
    else:
        print("❌ Language detection disable functionality failed!")
    
    # Re-enable language detection
    config_manager.update_language_config(detection_enabled=True)
    print("\n✅ Language detection re-enabled")
    
    # Test supported languages check
    print("\nSupported Languages:")
    supported_langs = language_service._get_supported_languages()
    for lang in supported_langs:
        print(f"  - {lang}")

if __name__ == "__main__":
    try:
        test_language_detection()
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc() 