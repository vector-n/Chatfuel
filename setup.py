#!/usr/bin/env python3
"""
Quick Setup Script for ChatFuel Bot
Generates encryption key and validates basic configuration
"""

import sys
import os
from pathlib import Path

def generate_encryption_key():
    """Generate a new Fernet encryption key"""
    try:
        from cryptography.fernet import Fernet
        key = Fernet.generate_key().decode()
        return key
    except ImportError:
        print("❌ Error: cryptography package not installed")
        print("Run: pip install cryptography")
        sys.exit(1)

def create_env_file():
    """Create .env file from .env.example if it doesn't exist"""
    env_example = Path(".env.example")
    env_file = Path(".env")
    
    if not env_example.exists():
        print("❌ Error: .env.example not found")
        return False
    
    if env_file.exists():
        response = input(".env file already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("✅ Keeping existing .env file")
            return False
    
    # Copy example to .env
    with open(env_example, 'r') as f:
        content = f.read()
    
    with open(env_file, 'w') as f:
        f.write(content)
    
    print("✅ Created .env file from .env.example")
    return True

def main():
    print("=" * 60)
    print("ChatFuel Bot - Quick Setup")
    print("=" * 60)
    print()
    
    # Generate encryption key
    print("📝 Generating encryption key...")
    encryption_key = generate_encryption_key()
    print(f"✅ Encryption key generated:")
    print(f"   {encryption_key}")
    print()
    
    # Create .env file
    print("📝 Setting up .env file...")
    created = create_env_file()
    print()
    
    if created or not Path(".env").exists():
        print("⚠️  Next steps:")
        print("   1. Open .env file")
        print("   2. Replace 'your_encryption_key_here' with the key above")
        print("   3. Add your BOT_TOKEN from @BotFather")
        print("   4. Add your BOT_USERNAME")
        print("   5. Add your ADMIN_USER_IDS (get from @userinfobot)")
        print("   6. Choose deployment platform and update WEBHOOK_URL")
    else:
        print("⚠️  Update your existing .env file with:")
        print(f"   ENCRYPTION_KEY={encryption_key}")
    
    print()
    print("=" * 60)
    print("Setup complete! Next: Deploy to Render/Fly.io/Koyeb")
    print("See DEPLOYMENT_GUIDE.md for detailed instructions")
    print("=" * 60)

if __name__ == "__main__":
    main()
