#!/usr/bin/env python
"""
Database restoration script for WhatsApp OpenAI Bot

This script demonstrates how to restore the database from a backup SQL file.
"""

import os
import subprocess
import sys
from pathlib import Path
from whatsapp_bot.utils.logging_config import setup_logging, get_logger

# Initialize logging
setup_logging("INFO")
logger = get_logger(__name__)

def restore_database(backup_file: str, database_url: str) -> bool:
    """
    Restore database from a backup file
    
    Args:
        backup_file: Path to the backup file
        database_url: PostgreSQL connection URL
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Extract database name from URL
        db_name = database_url.split('/')[-1]
        
        logger.info(f"Restoring database '{db_name}' from backup file: {backup_file}")
        
        # Check if backup file exists
        if not Path(backup_file).exists():
            logger.error(f"Error: Backup file not found at {backup_file}")
            return False
        
        # Run psql command to restore
        result = subprocess.run(['psql', database_url, '-f', backup_file], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("Database restoration completed successfully!")
            return True
        else:
            logger.error("Database restoration failed.")
            logger.error(f"Error output: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Error during database restoration: {str(e)}")
        return False

def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Restore WhatsApp Bot Database')
    parser.add_argument('backup_file', help='Path to the backup file')
    parser.add_argument('--database-url', help='Database URL (optional, uses DATABASE_URL env var if not provided)')
    
    args = parser.parse_args()
    
    # Get database URL
    database_url = args.database_url or os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("Error: Database URL not provided and DATABASE_URL environment variable not set")
        sys.exit(1)
    
    # Restore database
    if restore_database(args.backup_file, database_url):
        logger.info("Database restoration successful!")
        sys.exit(0)
    else:
        logger.error("Database restoration failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 