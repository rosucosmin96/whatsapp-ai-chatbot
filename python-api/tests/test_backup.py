#!/usr/bin/env python3
"""
Test script for the automated backup service
"""

import os
import sys
from dotenv import load_dotenv

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from whatsapp_bot.services.backup_service import DatabaseBackupService
from whatsapp_bot.utils.logging_config import setup_logging, get_logger

# Initialize logging
setup_logging("INFO")
logger = get_logger(__name__)

def test_backup_service():
    """Test the database backup service functionality"""
    
    # Load environment variables
    load_dotenv()
    
    # Check if DATABASE_URL is set
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("❌ Error: DATABASE_URL environment variable not set")
        return False
    
    logger.info("🔧 Testing Database Backup Service")
    logger.info("=" * 50)
    
    try:
        # Initialize backup service
        backup_service = DatabaseBackupService(database_url)
        logger.info("✅ Backup service initialized successfully")
        
        # Test database connection
        if backup_service.test_connection():
            logger.info("✅ Database connection test passed")
        else:
            logger.error("❌ Database connection test failed")
            return False
        
        # Test backup creation
        logger.info("\n📦 Creating test backup...")
        backup_path = backup_service.create_backup()
        if backup_path:
            logger.info(f"✅ Test backup created: {backup_path}")
        
        # Test listing backups
        logger.info("\n📋 Listing available backups:")
        backups = backup_service.list_backups()
        for backup in backups:
            logger.info(f"  📄 {backup['filename']} - {backup['size_kb']:.2f} KB - {backup['created']}")
        
        # Test cleanup
        logger.info("\n🧹 Testing cleanup...")
        deleted = backup_service.cleanup_old_backups()
        logger.info(f"✅ Cleanup completed - {deleted} old files deleted")
        
        logger.info("\n🎉 All backup service tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Backup service test failed: {str(e)}")
        return False

def main():
    """Main test function"""
    logger.info("🧪 WhatsApp OpenAI Bot - Backup Service Test")
    logger.info("=" * 60)
    
    if test_backup_service():
        logger.info("\n✅ All tests passed successfully!")
        sys.exit(0)
    else:
        logger.error("\n❌ Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 