#!/usr/bin/env python
"""
Database setup script for WhatsApp OpenAI Bot

Usage:
    - For regular setup: python setup_database.py
    - To restore from backup: python setup_database.py --restore --backup_file path/to/backup.sql
"""

import sys
import argparse

def main():
    parser = argparse.ArgumentParser(description='Database setup for WhatsApp OpenAI Bot')
    parser.add_argument('--restore', action='store_true', help='Restore database from backup')
    parser.add_argument('--backup_file', default='python-api/chatbot_backup.sql', 
                        help='Path to backup SQL file')
    parser.add_argument('--db_name', default='chatbot', help='Database name')
    parser.add_argument('--db_user', default='chatbot_user', help='Database user')
    parser.add_argument('--db_password', default='securepass', help='Database password')
    parser.add_argument('--db_host', default='localhost', help='Database host')
    
    args = parser.parse_args()
    
    # Pass all arguments to the setup_db module
    from whatsapp_bot.database.setup_db import main as setup_main
    
    # Override sys.argv to pass our parsed arguments to the setup_db main function
    sys.argv = [sys.argv[0]]
    if args.restore:
        sys.argv.append('--restore')
    if args.backup_file:
        sys.argv.extend(['--backup_file', args.backup_file])
    if args.db_name:
        sys.argv.extend(['--db_name', args.db_name])
    if args.db_user:
        sys.argv.extend(['--db_user', args.db_user])
    if args.db_password:
        sys.argv.extend(['--db_password', args.db_password])
    if args.db_host:
        sys.argv.extend(['--db_host', args.db_host])
    
    setup_main()

if __name__ == "__main__":
    main() 