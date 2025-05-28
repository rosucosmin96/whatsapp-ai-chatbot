import argparse
import os
import subprocess
import sys
from dotenv import load_dotenv
from pathlib import Path
from whatsapp_bot.utils.logging_config import setup_logging, get_logger

# Initialize logging
setup_logging("INFO")
logger = get_logger(__name__)

def run_command(command, capture_output=True):
    """Run a shell command and return the result"""
    try:
        result = subprocess.run(command, shell=True, capture_output=capture_output, text=True)
        if result.stdout:
            logger.debug(result.stdout)
        if result.stderr:
            logger.warning(result.stderr)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        logger.error(f"Error running command '{command}': {str(e)}")
        return False, "", str(e)

def setup_database(db_name, db_user, db_password, db_host="localhost"):
    """Setup PostgreSQL database for the WhatsApp chatbot"""
    logger.info(f"Setting up PostgreSQL database '{db_name}' for user '{db_user}'")
    
    # Create database and user using psql commands
    commands = [
        # Create user if not exists
        f"PGPASSWORD=postgres psql -h {db_host} -U postgres -c \"SELECT 1 FROM pg_roles WHERE rolname='{db_user}'\" | grep -q 1 || PGPASSWORD=postgres psql -h {db_host} -U postgres -c \"CREATE USER {db_user} WITH PASSWORD '{db_password}';\"",
        
        # Create database if not exists
        f"PGPASSWORD=postgres psql -h {db_host} -U postgres -c \"SELECT 1 FROM pg_database WHERE datname='{db_name}'\" | grep -q 1 || PGPASSWORD=postgres psql -h {db_host} -U postgres -c \"CREATE DATABASE {db_name};\"",
        
        # Grant privileges
        f"PGPASSWORD=postgres psql -h {db_host} -U postgres -c \"GRANT ALL PRIVILEGES ON DATABASE {db_name} TO {db_user};\""
    ]
    
    # Run commands
    for command in commands:
        logger.info(f"Running: {command}")
        success, stdout, stderr = run_command(command)
        if not success:
            logger.error(f"Error executing command. Return code: {success}")
            return False
    
    # Generate connection string
    connection_string = f"postgresql://{db_user}:{db_password}@{db_host}/{db_name}"
    
    # Update .env file
    update_env_file(connection_string)
    
    logger.info(f"Database setup complete. Connection string: {connection_string}")
    return True

def update_env_file(connection_string):
    """Update .env file with database connection string"""
    env_path = Path('.env')
    
    if env_path.exists():
        # Read existing .env file
        with open(env_path, 'r') as f:
            lines = f.readlines()
        
        # Check if DATABASE_URL exists and update it
        database_url_exists = False
        new_lines = []
        
        for line in lines:
            if line.startswith('DATABASE_URL='):
                new_lines.append(f'DATABASE_URL={connection_string}\n')
                database_url_exists = True
            else:
                new_lines.append(line)
        
        # Add DATABASE_URL if it doesn't exist
        if not database_url_exists:
            new_lines.append(f'DATABASE_URL={connection_string}\n')
        
        # Write updated content back to .env
        with open(env_path, 'w') as f:
            f.writelines(new_lines)
    else:
        # Create new .env file
        with open(env_path, 'w') as f:
            f.write(f'DATABASE_URL={connection_string}\n')
    
    logger.info(f"Updated .env file with DATABASE_URL")

def restore_from_backup(db_name, db_user, db_password, db_host="localhost", backup_file=None):
    """Restore PostgreSQL database from a backup SQL file"""
    if backup_file is None or not os.path.exists(backup_file):
        logger.error(f"Error: Backup file not found or not specified")
        return False

    logger.info(f"Restoring database '{db_name}' from backup file '{backup_file}'")
    
    # First ensure the database exists
    if not setup_database(db_name, db_user, db_password, db_host):
        logger.error("Failed to set up the database before restoration")
        return False
    
    # Restore command
    restore_command = f"PGPASSWORD={db_password} psql -h {db_host} -U {db_user} -d {db_name} -f {backup_file}"
    
    logger.info(f"Running restore command...")
    success, stdout, stderr = run_command(restore_command)
    
    if not success:
        logger.error(f"Error restoring database. Return code: {success}")
        return False
    
    logger.info(f"Database restored successfully from {backup_file}")
    return True

def main():
    """Main function to run the database setup"""
    parser = argparse.ArgumentParser(description='Setup PostgreSQL database for WhatsApp chatbot')
    parser.add_argument('--db_name', default='chatbot', help='Database name')
    parser.add_argument('--db_user', default='chatbot_user', help='Database user')
    parser.add_argument('--db_password', default='securepass', help='Database password')
    parser.add_argument('--db_host', default='localhost', help='Database host')
    parser.add_argument('--restore', action='store_true', help='Restore database from backup')
    parser.add_argument('--backup_file', default='../chatbot_backup.sql', help='Path to backup SQL file')
    
    args = parser.parse_args()
    
    if args.restore:
        # Get absolute path of backup file
        backup_path = os.path.abspath(os.path.join(os.path.dirname(__file__), args.backup_file))
        
        if restore_from_backup(args.db_name, args.db_user, args.db_password, args.db_host, backup_path):
            logger.info("Database restoration successful!")
        else:
            logger.error("Database restoration failed.")
            sys.exit(1)
    else:
        # Setup database
        if setup_database(args.db_name, args.db_user, args.db_password, args.db_host):
            logger.info("Database setup successful!")
            
            # Import and run init_db function
            try:
                from .database import init_db
                init_db()
                logger.info("Database tables initialized successfully!")
            except Exception as e:
                logger.error(f"Error initializing database tables: {str(e)}")
        else:
            logger.error("Database setup failed.")
            sys.exit(1)

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    main() 