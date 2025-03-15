"""
Custom exceptions for the DiscoSui application.

This module defines a comprehensive hierarchy of exceptions used throughout the application.
Each exception type provides specific error information and context to help with debugging
and error handling.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
import traceback

logger = logging.getLogger(__name__)

class ErrorContext:
    """Container for error context information."""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
        traceback_info: Optional[str] = None
    ):
        """Initialize error context.
        
        Args:
            message: Error message
            error_code: Optional error code for categorization
            details: Optional dictionary of additional error details
            timestamp: Optional timestamp of when the error occurred
            traceback_info: Optional traceback information
        """
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.timestamp = timestamp or datetime.now()
        self.traceback_info = traceback_info or traceback.format_exc()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert error context to dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation of error context
        """
        return {
            "message": self.message,
            "error_code": self.error_code,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "traceback": self.traceback_info
        }
        
    def __str__(self) -> str:
        """String representation of error context.
        
        Returns:
            str: Formatted error message
        """
        parts = [f"Error: {self.message}"]
        if self.error_code:
            parts.append(f"Code: {self.error_code}")
        if self.details:
            parts.append(f"Details: {self.details}")
        return " | ".join(parts)

class DiscoSuiError(Exception):
    """Base exception for DiscoSui.
    
    All application-specific exceptions should inherit from this class.
    """
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize base exception.
        
        Args:
            message: Error message
            error_code: Optional error code for categorization
            details: Optional dictionary of additional error details
        """
        self.context = ErrorContext(message, error_code, details)
        super().__init__(str(self.context))
        logger.error(f"DiscoSui Error: {self.context}")
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation of exception
        """
        return self.context.to_dict()

class ServiceError(DiscoSuiError):
    """Base exception for service-related errors.
    
    Used for errors that occur within application services.
    """
    
    def __init__(
        self,
        message: str,
        service_name: str,
        operation: Optional[str] = None,
        **kwargs
    ):
        """Initialize service error.
        
        Args:
            message: Error message
            service_name: Name of the service where the error occurred
            operation: Optional name of the operation that failed
            **kwargs: Additional keyword arguments for base class
        """
        details = kwargs.pop("details", {})
        details.update({
            "service_name": service_name,
            "operation": operation
        })
        super().__init__(message, details=details, **kwargs)

class EmailProcessingError(ServiceError):
    """Exception raised for errors in email processing service."""
    
    def __init__(
        self,
        message: str,
        email_id: Optional[str] = None,
        processing_stage: Optional[str] = None,
        **kwargs
    ):
        """Initialize email processing error.
        
        Args:
            message: Error message
            email_id: Optional ID of the email being processed
            processing_stage: Optional stage where processing failed
            **kwargs: Additional keyword arguments for base class
        """
        details = kwargs.pop("details", {})
        details.update({
            "email_id": email_id,
            "processing_stage": processing_stage
        })
        super().__init__(
            message,
            service_name="email_processing",
            details=details,
            **kwargs
        )

class EmailServiceError(ServiceError):
    """Exception raised for errors in email service operations."""
    
    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        email_id: Optional[str] = None,
        **kwargs
    ):
        """Initialize email service error.
        
        Args:
            message: Error message
            operation: Optional operation that failed
            email_id: Optional ID of the email being processed
            **kwargs: Additional keyword arguments for base class
        """
        details = kwargs.pop("details", {})
        details.update({
            "operation": operation,
            "email_id": email_id
        })
        super().__init__(
            message,
            service_name="email_service",
            details=details,
            **kwargs
        )

class EmailImportError(ServiceError):
    """Exception raised for errors during email import operations."""
    
    def __init__(
        self,
        message: str,
        source: Optional[str] = None,
        import_stage: Optional[str] = None,
        **kwargs
    ):
        """Initialize email import error.
        
        Args:
            message: Error message
            source: Optional source of the email being imported
            import_stage: Optional stage where import failed
            **kwargs: Additional keyword arguments for base class
        """
        details = kwargs.pop("details", {})
        details.update({
            "source": source,
            "import_stage": import_stage
        })
        super().__init__(
            message,
            service_name="email_import",
            details=details,
            **kwargs
        )

class AudioProcessingError(ServiceError):
    """Exception raised for errors in audio processing service."""
    
    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        processing_stage: Optional[str] = None,
        **kwargs
    ):
        """Initialize audio processing error.
        
        Args:
            message: Error message
            file_path: Optional path to the audio file
            processing_stage: Optional stage where processing failed
            **kwargs: Additional keyword arguments for base class
        """
        details = kwargs.pop("details", {})
        details.update({
            "file_path": file_path,
            "processing_stage": processing_stage
        })
        super().__init__(
            message,
            service_name="audio_processing",
            details=details,
            **kwargs
        )

class AudioServiceError(ServiceError):
    """Exception raised for errors in audio service operations."""
    
    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        audio_id: Optional[str] = None,
        **kwargs
    ):
        """Initialize audio service error.
        
        Args:
            message: Error message
            operation: Optional operation that failed
            audio_id: Optional ID of the audio being processed
            **kwargs: Additional keyword arguments for base class
        """
        details = kwargs.pop("details", {})
        details.update({
            "operation": operation,
            "audio_id": audio_id
        })
        super().__init__(
            message,
            service_name="audio_service",
            details=details,
            **kwargs
        )

class ContentManagementError(ServiceError):
    """Exception raised for errors in content management service."""
    
    def __init__(
        self,
        message: str,
        content_type: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs
    ):
        """Initialize content management error.
        
        Args:
            message: Error message
            content_type: Optional type of content being managed
            operation: Optional operation that failed
            **kwargs: Additional keyword arguments for base class
        """
        details = kwargs.pop("details", {})
        details.update({
            "content_type": content_type,
            "operation": operation
        })
        super().__init__(
            message,
            service_name="content_management",
            details=details,
            **kwargs
        )

class AnalysisError(ServiceError):
    """Exception raised for errors in analysis service."""
    
    def __init__(
        self,
        message: str,
        analysis_type: Optional[str] = None,
        data_source: Optional[str] = None,
        **kwargs
    ):
        """Initialize analysis error.
        
        Args:
            message: Error message
            analysis_type: Optional type of analysis being performed
            data_source: Optional source of data being analyzed
            **kwargs: Additional keyword arguments for base class
        """
        details = kwargs.pop("details", {})
        details.update({
            "analysis_type": analysis_type,
            "data_source": data_source
        })
        super().__init__(
            message,
            service_name="analysis",
            details=details,
            **kwargs
        )

class SemanticAnalysisError(AnalysisError):
    """Exception raised for errors in semantic analysis operations."""
    
    def __init__(
        self,
        message: str,
        analysis_type: Optional[str] = None,
        content_id: Optional[str] = None,
        **kwargs
    ):
        """Initialize semantic analysis error.
        
        Args:
            message: Error message
            analysis_type: Optional type of semantic analysis being performed
            content_id: Optional ID of the content being analyzed
            **kwargs: Additional keyword arguments for base class
        """
        details = kwargs.pop("details", {})
        details.update({
            "content_id": content_id
        })
        super().__init__(
            message,
            analysis_type=analysis_type,
            details=details,
            **kwargs
        )

class OrganizationError(ServiceError):
    """Exception raised for errors in organization service."""
    
    def __init__(
        self,
        message: str,
        organization_type: Optional[str] = None,
        target: Optional[str] = None,
        **kwargs
    ):
        """Initialize organization error.
        
        Args:
            message: Error message
            organization_type: Optional type of organization being performed
            target: Optional target being organized
            **kwargs: Additional keyword arguments for base class
        """
        details = kwargs.pop("details", {})
        details.update({
            "organization_type": organization_type,
            "target": target
        })
        super().__init__(
            message,
            service_name="organization",
            details=details,
            **kwargs
        )

class ConfigurationError(DiscoSuiError):
    """Exception raised for configuration-related errors."""
    
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        invalid_value: Optional[Any] = None,
        **kwargs
    ):
        """Initialize configuration error.
        
        Args:
            message: Error message
            config_key: Optional configuration key that caused the error
            invalid_value: Optional invalid value that caused the error
            **kwargs: Additional keyword arguments for base class
        """
        details = kwargs.pop("details", {})
        details.update({
            "config_key": config_key,
            "invalid_value": invalid_value
        })
        super().__init__(message, error_code="CONFIG_ERROR", details=details, **kwargs)

class ValidationError(DiscoSuiError):
    """Exception raised for validation errors."""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        constraints: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Initialize validation error.
        
        Args:
            message: Error message
            field: Optional field that failed validation
            constraints: Optional validation constraints that were violated
            **kwargs: Additional keyword arguments for base class
        """
        details = kwargs.pop("details", {})
        details.update({
            "field": field,
            "constraints": constraints
        })
        super().__init__(message, error_code="VALIDATION_ERROR", details=details, **kwargs)

class AuthenticationError(DiscoSuiError):
    """Exception raised for authentication-related errors."""
    
    def __init__(
        self,
        message: str,
        auth_type: Optional[str] = None,
        user_id: Optional[str] = None,
        **kwargs
    ):
        """Initialize authentication error.
        
        Args:
            message: Error message
            auth_type: Optional type of authentication that failed
            user_id: Optional ID of the user
            **kwargs: Additional keyword arguments for base class
        """
        details = kwargs.pop("details", {})
        details.update({
            "auth_type": auth_type,
            "user_id": user_id
        })
        super().__init__(message, error_code="AUTH_ERROR", details=details, **kwargs)

class ObsidianError(DiscoSuiError):
    """Exception raised for Obsidian-related errors."""
    
    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        vault_path: Optional[str] = None,
        **kwargs
    ):
        """Initialize Obsidian error.
        
        Args:
            message: Error message
            operation: Optional operation that failed
            vault_path: Optional path to the vault
            **kwargs: Additional keyword arguments for base class
        """
        details = kwargs.pop("details", {})
        details.update({
            "operation": operation,
            "vault_path": vault_path
        })
        super().__init__(message, error_code="OBSIDIAN_ERROR", details=details, **kwargs)

class ObsidianIOError(ObsidianError):
    """Exception raised for Obsidian I/O operations."""
    
    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        io_operation: Optional[str] = None,
        **kwargs
    ):
        """Initialize Obsidian I/O error.
        
        Args:
            message: Error message
            file_path: Optional path to the file
            io_operation: Optional I/O operation that failed
            **kwargs: Additional keyword arguments for base class
        """
        details = kwargs.pop("details", {})
        details.update({
            "file_path": file_path,
            "io_operation": io_operation
        })
        super().__init__(message, error_code="OBSIDIAN_IO_ERROR", details=details, **kwargs)

class DatabaseError(DiscoSuiError):
    """Exception raised for database-related errors."""
    
    def __init__(
        self,
        message: str,
        db_operation: Optional[str] = None,
        collection: Optional[str] = None,
        **kwargs
    ):
        """Initialize database error.
        
        Args:
            message: Error message
            db_operation: Optional database operation that failed
            collection: Optional collection being accessed
            **kwargs: Additional keyword arguments for base class
        """
        details = kwargs.pop("details", {})
        details.update({
            "db_operation": db_operation,
            "collection": collection
        })
        super().__init__(message, error_code="DB_ERROR", details=details, **kwargs)

class FileSystemError(DiscoSuiError):
    """Exception raised for file system-related errors."""
    
    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs
    ):
        """Initialize file system error.
        
        Args:
            message: Error message
            file_path: Optional path to the file
            operation: Optional operation that failed
            **kwargs: Additional keyword arguments for base class
        """
        details = kwargs.pop("details", {})
        details.update({
            "file_path": file_path,
            "operation": operation
        })
        super().__init__(message, error_code="FS_ERROR", details=details, **kwargs)

class TemplateError(DiscoSuiError):
    """Exception raised for template-related errors."""
    
    def __init__(self, message: str, template_name: str = None, operation: str = None, **kwargs):
        """Initialize the exception.
        
        Args:
            message: Error message
            template_name: Name of the template that caused the error
            operation: Operation that caused the error
            **kwargs: Additional error information
        """
        super().__init__(message)
        self.template_name = template_name
        self.operation = operation
        self.details = kwargs

class HierarchyError(DiscoSuiError):
    """Exception raised for hierarchy-related errors."""
    
    def __init__(
        self,
        message: str,
        node_path: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs
    ):
        """Initialize hierarchy error.
        
        Args:
            message: Error message
            node_path: Optional path in the hierarchy
            operation: Optional operation that failed
            **kwargs: Additional keyword arguments for base class
        """
        details = kwargs.pop("details", {})
        details.update({
            "node_path": node_path,
            "operation": operation
        })
        super().__init__(message, error_code="HIERARCHY_ERROR", details=details, **kwargs)

class TaggingError(DiscoSuiError):
    """Exception raised for tagging-related errors."""
    
    def __init__(
        self,
        message: str,
        tag: Optional[str] = None,
        note_path: Optional[str] = None,
        **kwargs
    ):
        """Initialize tagging error.
        
        Args:
            message: Error message
            tag: Optional tag that caused the error
            note_path: Optional path to the note
            **kwargs: Additional keyword arguments for base class
        """
        details = kwargs.pop("details", {})
        details.update({
            "tag": tag,
            "note_path": note_path
        })
        super().__init__(message, error_code="TAG_ERROR", details=details, **kwargs)

class SearchError(DiscoSuiError):
    """Exception raised for search-related errors."""
    
    def __init__(
        self,
        message: str,
        query: Optional[str] = None,
        search_type: Optional[str] = None,
        **kwargs
    ):
        """Initialize search error.
        
        Args:
            message: Error message
            query: Optional search query
            search_type: Optional type of search
            **kwargs: Additional keyword arguments for base class
        """
        details = kwargs.pop("details", {})
        details.update({
            "query": query,
            "search_type": search_type
        })
        super().__init__(message, error_code="SEARCH_ERROR", details=details, **kwargs)

class AudioTranscriptionError(DiscoSuiError):
    """Exception raised for audio transcription-related errors."""
    
    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        transcription_stage: Optional[str] = None,
        **kwargs
    ):
        """Initialize audio transcription error.
        
        Args:
            message: Error message
            file_path: Optional path to the audio file
            transcription_stage: Optional stage where transcription failed
            **kwargs: Additional keyword arguments for base class
        """
        details = kwargs.pop("details", {})
        details.update({
            "file_path": file_path,
            "transcription_stage": transcription_stage
        })
        super().__init__(message, error_code="TRANSCRIPTION_ERROR", details=details, **kwargs)

class IndexingError(DiscoSuiError):
    """Exception raised for indexing-related errors."""
    
    def __init__(
        self,
        message: str,
        index_type: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs
    ):
        """Initialize indexing error.
        
        Args:
            message: Error message
            index_type: Optional type of index
            operation: Optional operation that failed
            **kwargs: Additional keyword arguments for base class
        """
        details = kwargs.pop("details", {})
        details.update({
            "index_type": index_type,
            "operation": operation
        })
        super().__init__(message, error_code="INDEX_ERROR", details=details, **kwargs)

class NoteManagementError(DiscoSuiError):
    """Exception raised for errors in note management operations."""
    
    def __init__(
        self,
        message: str,
        note_path: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs
    ):
        """Initialize note management error.
        
        Args:
            message: Error message
            note_path: Optional path to the note
            operation: Optional operation that failed
            **kwargs: Additional keyword arguments for base class
        """
        details = kwargs.pop("details", {})
        details.update({
            "note_path": note_path,
            "operation": operation
        })
        super().__init__(message, details=details, **kwargs)

class NoteManipulationError(DiscoSuiError):
    """Exception raised for errors during note manipulation operations."""
    
    def __init__(
        self,
        message: str,
        note_path: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs
    ):
        """Initialize note manipulation error.
        
        Args:
            message: Error message
            note_path: Optional path to the note being manipulated
            operation: Optional operation that failed
            **kwargs: Additional keyword arguments for base class
        """
        details = kwargs.pop("details", {})
        details.update({
            "note_path": note_path,
            "operation": operation
        })
        super().__init__(message, details=details, **kwargs)

class LLMError(DiscoSuiError):
    """Raised when there's an error in LLM operations."""
    
    def __init__(
        self,
        message: str,
        model: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs
    ):
        """Initialize LLM error.
        
        Args:
            message: Error message
            model: Optional LLM model being used
            operation: Optional operation that failed
            **kwargs: Additional keyword arguments for base class
        """
        details = kwargs.pop("details", {})
        details.update({
            "model": model,
            "operation": operation
        })
        super().__init__(message, error_code="LLM_ERROR", details=details, **kwargs)

class RAGError(DiscoSuiError):
    """Raised when there's an error in RAG operations."""
    
    def __init__(
        self,
        message: str,
        stage: Optional[str] = None,
        query: Optional[str] = None,
        **kwargs
    ):
        """Initialize RAG error.
        
        Args:
            message: Error message
            stage: Optional RAG stage where the error occurred
            query: Optional query being processed
            **kwargs: Additional keyword arguments for base class
        """
        details = kwargs.pop("details", {})
        details.update({
            "stage": stage,
            "query": query
        })
        super().__init__(message, error_code="RAG_ERROR", details=details, **kwargs)

class RateLimitError(DiscoSuiError):
    """Raised when rate limit is exceeded."""
    
    def __init__(
        self,
        message: str,
        limit: Optional[int] = None,
        window: Optional[int] = None,
        **kwargs
    ):
        """Initialize rate limit error.
        
        Args:
            message: Error message
            limit: Optional rate limit that was exceeded
            window: Optional time window in seconds
            **kwargs: Additional keyword arguments for base class
        """
        details = kwargs.pop("details", {})
        details.update({
            "limit": limit,
            "window": window
        })
        super().__init__(message, error_code="RATE_LIMIT_ERROR", details=details, **kwargs)

class ResourceNotFoundError(DiscoSuiError):
    """Raised when a requested resource is not found."""
    
    def __init__(
        self,
        message: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        **kwargs
    ):
        """Initialize resource not found error.
        
        Args:
            message: Error message
            resource_type: Optional type of resource
            resource_id: Optional ID of the resource
            **kwargs: Additional keyword arguments for base class
        """
        details = kwargs.pop("details", {})
        details.update({
            "resource_type": resource_type,
            "resource_id": resource_id
        })
        super().__init__(message, error_code="NOT_FOUND", details=details, **kwargs)

class NoteNotFoundError(ResourceNotFoundError):
    """Raised when a requested note is not found."""
    
    def __init__(self, message: str, note_path: Optional[str] = None, **kwargs):
        """Initialize note not found error.
        
        Args:
            message: Error message
            note_path: Optional path to the note
            **kwargs: Additional keyword arguments for base class
        """
        super().__init__(
            message,
            resource_type="note",
            resource_id=note_path,
            **kwargs
        )

class NoteAlreadyExistsError(DiscoSuiError):
    """Raised when attempting to create a note that already exists."""
    
    def __init__(self, message: str, note_path: Optional[str] = None, **kwargs):
        """Initialize note already exists error.
        
        Args:
            message: Error message
            note_path: Optional path to the note
            **kwargs: Additional keyword arguments for base class
        """
        details = kwargs.pop("details", {})
        details.update({"note_path": note_path})
        super().__init__(message, error_code="NOTE_EXISTS", details=details, **kwargs)

class TemplateNotFoundError(ResourceNotFoundError):
    """Raised when a requested template is not found."""
    
    def __init__(self, message: str, template_name: Optional[str] = None, **kwargs):
        """Initialize template not found error.
        
        Args:
            message: Error message
            template_name: Optional name of the template
            **kwargs: Additional keyword arguments for base class
        """
        super().__init__(
            message,
            resource_type="template",
            resource_id=template_name,
            **kwargs
        )

class FrontmatterError(ValidationError):
    """Raised when there's an error in note frontmatter."""
    
    def __init__(
        self,
        message: str,
        note_path: Optional[str] = None,
        frontmatter_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Initialize frontmatter error.
        
        Args:
            message: Error message
            note_path: Optional path to the note
            frontmatter_data: Optional frontmatter data that caused the error
            **kwargs: Additional keyword arguments for base class
        """
        details = kwargs.pop("details", {})
        details.update({
            "note_path": note_path,
            "frontmatter_data": frontmatter_data
        })
        super().__init__(message, field="frontmatter", details=details, **kwargs)

class PermissionError(DiscoSuiError):
    """Raised when there's a permission error."""
    
    def __init__(
        self,
        message: str,
        required_permission: Optional[str] = None,
        user_id: Optional[str] = None,
        **kwargs
    ):
        """Initialize permission error.
        
        Args:
            message: Error message
            required_permission: Optional required permission
            user_id: Optional ID of the user
            **kwargs: Additional keyword arguments for base class
        """
        details = kwargs.pop("details", {})
        details.update({
            "required_permission": required_permission,
            "user_id": user_id
        })
        super().__init__(message, error_code="PERMISSION_ERROR", details=details, **kwargs)

class NetworkError(DiscoSuiError):
    """Raised when there's a network-related error."""
    
    def __init__(
        self,
        message: str,
        url: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs
    ):
        """Initialize network error.
        
        Args:
            message: Error message
            url: Optional URL that caused the error
            operation: Optional network operation that failed
            **kwargs: Additional keyword arguments for base class
        """
        details = kwargs.pop("details", {})
        details.update({
            "url": url,
            "operation": operation
        })
        super().__init__(message, error_code="NETWORK_ERROR", details=details, **kwargs)

class TimeoutError(DiscoSuiError):
    """Raised when an operation times out."""
    
    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
        **kwargs
    ):
        """Initialize timeout error.
        
        Args:
            message: Error message
            operation: Optional operation that timed out
            timeout_seconds: Optional timeout duration in seconds
            **kwargs: Additional keyword arguments for base class
        """
        details = kwargs.pop("details", {})
        details.update({
            "operation": operation,
            "timeout_seconds": timeout_seconds
        })
        super().__init__(message, error_code="TIMEOUT", details=details, **kwargs)

class FolderNotFoundError(ResourceNotFoundError):
    """Raised when a requested folder is not found."""
    
    def __init__(self, message: str, folder_path: Optional[str] = None, **kwargs):
        """Initialize folder not found error.
        
        Args:
            message: Error message
            folder_path: Optional path to the folder
            **kwargs: Additional keyword arguments for base class
        """
        super().__init__(
            message,
            resource_type="folder",
            resource_id=folder_path,
            **kwargs
        )

class ToolError(DiscoSuiError):
    """Exception raised for errors in tool execution."""
    
    def __init__(
        self,
        message: str,
        tool_name: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs
    ):
        """Initialize tool error.
        
        Args:
            message: Error message
            tool_name: Optional name of the tool where the error occurred
            operation: Optional operation that failed
            **kwargs: Additional keyword arguments for base class
        """
        details = kwargs.pop("details", {})
        details.update({
            "tool_name": tool_name,
            "operation": operation
        })
        super().__init__(
            message,
            details=details,
            **kwargs
        ) 