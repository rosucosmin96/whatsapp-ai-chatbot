#!/usr/bin/env python3
"""
Automated Database Backup Service for WhatsApp OpenAI Bot

This service provides:
- Scheduled hourly database backups
- Automatic cleanup of old backups
- Manual backup functionality
- Backup restoration utilities
"""

import os
import subprocess
import schedule
import time
import signal
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path
from whatsapp_bot.utils.logging_config import get_logger

# Setup logging
logger = get_logger(__name__)


class DatabaseBackupService:
    """Service for automated database backups with retention management"""
    
    def __init__(self, database_url: str, backup_dir: str = "backups"):
        """
        Initialize the backup service
        
        Args:
            database_url: PostgreSQL connection URL
            backup_dir: Directory to store backup files
        """
        self.database_url = database_url
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        
        # Configuration from environment variables
        self.backup_schedule_hours = int(os.getenv('BACKUP_SCHEDULE_HOURS', '24'))
        self.backup_retention_hours = int(os.getenv('BACKUP_RETENTION_HOURS', '168'))  # 7 days
        
        logger.info(f"Backup service initialized - Schedule: {self.backup_schedule_hours}h, Retention: {self.backup_retention_hours}h")
        
    def create_backup(self) -> Optional[str]:
        """
        Create a database backup using pg_dump
        
        Returns:
            Path to the backup file if successful, None otherwise
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"whatsapp_bot_backup_{timestamp}.sql"
            backup_path = self.backup_dir / backup_filename
            
            # Extract database connection details from URL
            # Format: postgresql://user:password@host:port/database
            url_parts = self.database_url.replace("postgresql://", "").split("/")
            db_name = url_parts[-1]
            connection_part = url_parts[0]
            
            if "@" in connection_part:
                auth_part, host_part = connection_part.split("@")
                if ":" in auth_part:
                    username, password = auth_part.split(":", 1)
                else:
                    username = auth_part
                    password = ""
            else:
                host_part = connection_part
                username = "postgres"
                password = ""
            
            if ":" in host_part:
                host, port = host_part.split(":")
            else:
                host = host_part
                port = "5432"
            
            # Set environment variables for pg_dump
            env = os.environ.copy()
            if password:
                env['PGPASSWORD'] = password
            
            # Run pg_dump command
            cmd = [
                'pg_dump',
                '-h', host,
                '-p', port,
                '-U', username,
                '-d', db_name,
                '--no-password',
                '--verbose',
                '--clean',
                '--if-exists',
                '--create',
                '-f', str(backup_path)
            ]
            
            logger.info(f"Creating backup: {backup_filename}")
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Verify backup file was created and has content
                if backup_path.exists() and backup_path.stat().st_size > 0:
                    logger.info(f"Backup created successfully: {backup_path}")
                    return str(backup_path)
                else:
                    logger.error("Backup file was not created or is empty")
                    return None
            else:
                logger.error(f"pg_dump failed with return code {result.returncode}")
                logger.error(f"Error output: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating backup: {str(e)}")
            return None
    
    def restore_backup(self, backup_file: str) -> bool:
        """
        Restore database from a backup file
        
        Args:
            backup_file: Path to the backup file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            backup_path = Path(backup_file)
            if not backup_path.exists():
                logger.error(f"Backup file not found: {backup_file}")
                return False
            
            # Extract database connection details
            url_parts = self.database_url.replace("postgresql://", "").split("/")
            db_name = url_parts[-1]
            connection_part = url_parts[0]
            
            if "@" in connection_part:
                auth_part, host_part = connection_part.split("@")
                if ":" in auth_part:
                    username, password = auth_part.split(":", 1)
                else:
                    username = auth_part
                    password = ""
            else:
                host_part = connection_part
                username = "postgres"
                password = ""
            
            if ":" in host_part:
                host, port = host_part.split(":")
            else:
                host = host_part
                port = "5432"
            
            # Set environment variables
            env = os.environ.copy()
            if password:
                env['PGPASSWORD'] = password
            
            # Run psql command to restore
            cmd = [
                'psql',
                '-h', host,
                '-p', port,
                '-U', username,
                '-d', db_name,
                '-f', str(backup_path)
            ]
            
            logger.info(f"Restoring from backup: {backup_file}")
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("Database restored successfully")
                return True
            else:
                logger.error(f"Restore failed with return code {result.returncode}")
                logger.error(f"Error output: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error restoring backup: {str(e)}")
            return False
    
    def list_backups(self) -> List[Dict[str, str]]:
        """
        List all available backup files
        
        Returns:
            List of backup file information
        """
        try:
            backups = []
            for backup_file in self.backup_dir.glob("*.sql"):
                stat = backup_file.stat()
                backups.append({
                    'filename': backup_file.name,
                    'path': str(backup_file),
                    'size_kb': stat.st_size / 1024,
                    'created': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                })
            
            # Sort by creation time (newest first)
            backups.sort(key=lambda x: x['created'], reverse=True)
            return backups
            
        except Exception as e:
            logger.error(f"Error listing backups: {str(e)}")
            return []
    
    def cleanup_old_backups(self) -> int:
        """
        Remove backup files older than retention period
        
        Returns:
            Number of files deleted
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=self.backup_retention_hours)
            deleted_count = 0
            
            for backup_file in self.backup_dir.glob("*.sql"):
                file_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
                if file_time < cutoff_time:
                    backup_file.unlink()
                    deleted_count += 1
                    logger.debug(f"Deleted old backup: {backup_file.name}")
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old backup files")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
            return 0
    
    def test_connection(self) -> bool:
        """
        Test database connection
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Extract connection details
            url_parts = self.database_url.replace("postgresql://", "").split("/")
            db_name = url_parts[-1]
            connection_part = url_parts[0]
            
            if "@" in connection_part:
                auth_part, host_part = connection_part.split("@")
                if ":" in auth_part:
                    username, password = auth_part.split(":", 1)
                else:
                    username = auth_part
                    password = ""
            else:
                host_part = connection_part
                username = "postgres"
                password = ""
            
            if ":" in host_part:
                host, port = host_part.split(":")
            else:
                host = host_part
                port = "5432"
            
            # Set environment variables
            env = os.environ.copy()
            if password:
                env['PGPASSWORD'] = password
            
            # Test connection with a simple query
            cmd = [
                'psql',
                '-h', host,
                '-p', port,
                '-U', username,
                '-d', db_name,
                '-c', 'SELECT 1;'
            ]
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.debug("Database connection test successful")
                return True
            else:
                logger.error(f"Database connection test failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error testing connection: {str(e)}")
            return False
    
    def scheduled_backup(self):
        """Perform a scheduled backup with cleanup"""
        logger.info("Starting scheduled backup...")
        
        # Create backup
        backup_path = self.create_backup()
        if backup_path:
            logger.info(f"Scheduled backup completed: {backup_path}")
        else:
            logger.error("Scheduled backup failed")
        
        # Cleanup old backups
        deleted = self.cleanup_old_backups()
        if deleted > 0:
            logger.info(f"Cleaned up {deleted} old backup files")
    
    def start_scheduler(self):
        """Start the backup scheduler"""
        # Schedule backup
        schedule.every(self.backup_schedule_hours).hours.do(self.scheduled_backup)
        
        logger.info(f"Backup scheduler started - running every {self.backup_schedule_hours} hours")
        
        # Run initial backup
        self.scheduled_backup()


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logger.info("Received shutdown signal, stopping backup scheduler...")
    sys.exit(0)


def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Database Backup Service')
    parser.add_argument('command', choices=['backup', 'restore', 'list', 'cleanup', 'test', 'schedule'],
                       help='Command to execute')
    parser.add_argument('--file', help='Backup file path (for restore command)')
    
    args = parser.parse_args()
    
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("DATABASE_URL environment variable not set")
        return
    
    # Initialize service
    service = DatabaseBackupService(database_url)
    
    if args.command == 'backup':
        backup_path = service.create_backup()
        if backup_path:
            logger.info(f"Backup created: {backup_path}")
        else:
            logger.error("Backup failed")
    
    elif args.command == 'restore':
        if not args.file:
            logger.error("--file argument required for restore command")
            return
        
        if service.restore_backup(args.file):
            logger.info("Restore completed successfully")
        else:
            logger.error("Restore failed")
    
    elif args.command == 'list':
        backups = service.list_backups()
        if backups:
            logger.info("Available backups:")
            for backup in backups:
                logger.info(f"  {backup['filename']} - {backup['size_kb']:.2f} KB - {backup['created']}")
        else:
            logger.info("No backups found")
    
    elif args.command == 'cleanup':
        deleted = service.cleanup_old_backups()
        logger.info(f"Deleted {deleted} old backup files")
    
    elif args.command == 'test':
        if service.test_connection():
            logger.info("Database connection successful")
        else:
            logger.error("Database connection failed")
    
    elif args.command == 'schedule':
        # Set up signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        logger.info("Starting backup scheduler...")
        service.start_scheduler()
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("\nScheduler stopped")
    
    else:
        logger.error(f"Unknown command: {args.command}")
        logger.info("Available commands: backup, restore, list, cleanup, test, schedule")


if __name__ == "__main__":
    # Initialize logging for standalone usage
    from whatsapp_bot.utils.logging_config import setup_logging
    setup_logging("INFO")
    
    main() 