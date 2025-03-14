"""
Email service for processing and integrating emails into the Obsidian vault.
"""

from .processor import EmailProcessor
from .importer import EmailImporter
from .service import EmailService

__all__ = ['EmailProcessor', 'EmailImporter', 'EmailService']
