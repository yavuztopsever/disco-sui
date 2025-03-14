from typing import Dict, Any, List, Optional
from pathlib import Path
from .base_tools import BaseTool
import email
import os
import json
from datetime import datetime
from email import policy
from email.parser import BytesParser
import mailparser
from ..core.tool_interfaces import EmailToolInterface
from ..core.exceptions import EmailProcessingError
from ..services.email_processing import EmailProcessor

class ProcessEmailTool(EmailToolInterface):
    """Tool for processing email content."""
    name = "process_email"
    description = "Process and analyze email content"
    
    async def forward(
        self,
        email_content: str,
        extract_attachments: bool = True,
        analyze_content: bool = True
    ) -> Dict[str, Any]:
        """Process and analyze email content.
        
        Args:
            email_content: Raw email content to process
            extract_attachments: Whether to extract attachments
            analyze_content: Whether to analyze email content
            
        Returns:
            Dictionary containing processed email data
        """
        return await self.process_email(email_content, extract_attachments, analyze_content)

class ExtractEmailMetadataTool(EmailToolInterface):
    """Tool for extracting email metadata."""
    name = "extract_email_metadata"
    description = "Extract metadata from email content"
    
    async def forward(
        self,
        email_content: str
    ) -> Dict[str, Any]:
        """Extract metadata from email content.
        
        Args:
            email_content: Raw email content
            
        Returns:
            Dictionary containing email metadata
        """
        return await self.extract_metadata(email_content)

class ConvertEmailToNoteTool(EmailToolInterface):
    """Tool for converting email to note format."""
    name = "convert_email_to_note"
    description = "Convert email content to note format"
    
    async def forward(
        self,
        email_content: str,
        include_attachments: bool = True,
        template_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Convert email content to note format.
        
        Args:
            email_content: Raw email content
            include_attachments: Whether to include attachments
            template_name: Optional template to use for conversion
            
        Returns:
            Dictionary containing converted note data
        """
        return await self.convert_to_note(email_content, include_attachments, template_name)

class AnalyzeEmailThreadTool(EmailToolInterface):
    """Tool for analyzing email thread structure."""
    name = "analyze_email_thread"
    description = "Analyze email thread structure and relationships"
    
    async def forward(
        self,
        thread_emails: List[str]
    ) -> Dict[str, Any]:
        """Analyze email thread structure.
        
        Args:
            thread_emails: List of raw email contents in thread
            
        Returns:
            Dictionary containing thread analysis
        """
        return await self.analyze_thread(thread_emails)

class ListEmailFilesTool(EmailToolInterface):
    """Tool for listing email files."""
    name = "list_email_files"
    description = "List email files in the vault"
    
    async def forward(
        self,
        folder: Optional[str] = None,
        include_processed: bool = False
    ) -> Dict[str, Any]:
        """List email files in the vault.
        
        Args:
            folder: Optional folder to search in
            include_processed: Whether to include already processed emails
            
        Returns:
            Dictionary containing list of email files
        """
        return await self.list_email_files(folder, include_processed)

class GetEmailNoteTool(EmailToolInterface):
    """Tool for retrieving email notes."""
    name = "get_email_note"
    description = "Get note associated with an email"
    
    async def forward(
        self,
        email_path: str
    ) -> Dict[str, Any]:
        """Get note associated with an email.
        
        Args:
            email_path: Path to the email file
            
        Returns:
            Dictionary containing note data
        """
        return await self.get_email_note(email_path)

class ExportEmailsTool(EmailToolInterface):
    """Tool for exporting emails to various formats."""
    name = "export_emails"
    description = "Export emails to external formats"
    
    async def forward(
        self,
        target_format: str,
        email_paths: List[str],
        output_path: str
    ) -> Dict[str, Any]:
        """Export emails to external formats.
        
        Args:
            target_format: Format to export to (e.g., 'mbox', 'eml', 'pdf')
            email_paths: List of email paths to export
            output_path: Path to export emails to
            
        Returns:
            Dictionary containing export results
        """
        return await self.export_emails(target_format, email_paths, output_path) 