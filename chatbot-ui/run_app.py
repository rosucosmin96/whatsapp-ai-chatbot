#!/usr/bin/env python3
"""
Run script for the WhatsApp OpenAI Bot Chainlit UI

This script provides an easy way to start the Chainlit application.
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Main function to run the Chainlit app"""
    # Get the directory of this script
    script_dir = Path(__file__).parent
    
    # Path to the main app file (direct file path, not module)
    app_file = script_dir / "src" / "chatbot_ui" / "app.py"
    
    # Environment variables with defaults
    host = os.getenv("CHAINLIT_HOST", "0.0.0.0")
    port = os.getenv("CHAINLIT_PORT", "8080")
    api_url = os.getenv("API_BASE_URL", "http://localhost:8000")
    phone = os.getenv("DEFAULT_PHONE", "+1234567890")
    
    print("🚀 Starting WhatsApp OpenAI Bot Chainlit UI")
    print(f"📡 API URL: {api_url}")
    print(f"📱 Default Phone: {phone}")
    print(f"🌐 UI will be available at: http://{host}:{port}")
    print("-" * 50)
    
    # Check if the app file exists
    if not app_file.exists():
        print(f"❌ App file not found: {app_file}")
        print("Make sure the src/chatbot_ui/app.py file exists")
        sys.exit(1)
    
    # Change to the script directory
    os.chdir(script_dir)
    
    # Build the chainlit command with direct file path
    cmd = [
        "chainlit", "run", 
        str(app_file),  # Use direct file path
        "--host", host,
        "--port", port
    ]
    
    try:
        # Run the chainlit application
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running Chainlit: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Shutting down Chainlit UI...")
        sys.exit(0)
    except FileNotFoundError:
        print("❌ Chainlit not found. Please install requirements first:")
        print("   pip install -r requirements.txt")
        sys.exit(1)


if __name__ == "__main__":
    main() 