"""
Services package for WhatsApp OpenAI Bot

This package contains external services and utilities:
- backup_service: Automated database backup functionality
- language_service: Language detection and management functionality
"""

from .backup_service import DatabaseBackupService
from .language_service import LanguageDetectionService

__all__ = ["DatabaseBackupService", "LanguageDetectionService"] 