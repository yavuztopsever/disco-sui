"""
Custom exceptions for the DiscoSui application.
"""

class DiscoSuiError(Exception):
    """Base exception for DiscoSui."""
    pass

class ServiceError(DiscoSuiError):
    """Base exception for service-related errors."""
    pass

class EmailProcessingError(ServiceError):
    """Exception raised for errors in email processing service."""
    pass

class AudioProcessingError(ServiceError):
    """Exception raised for errors in audio processing service."""
    pass

class ContentManagementError(ServiceError):
    """Exception raised for errors in content management service."""
    pass

class AnalysisError(ServiceError):
    """Exception raised for errors in analysis service."""
    pass

class OrganizationError(ServiceError):
    """Exception raised for errors in organization service."""
    pass

class ConfigurationError(DiscoSuiError):
    """Exception raised for configuration-related errors."""
    pass

class ValidationError(DiscoSuiError):
    """Exception raised for validation errors."""
    pass

class AuthenticationError(DiscoSuiError):
    """Exception raised for authentication-related errors."""
    pass

class ObsidianError(DiscoSuiError):
    """Exception raised for Obsidian-related errors."""
    pass

class DatabaseError(DiscoSuiError):
    """Exception raised for database-related errors."""
    pass

class FileSystemError(DiscoSuiError):
    """Exception raised for file system-related errors."""
    pass

class TemplateError(DiscoSuiError):
    """Exception raised for template-related errors."""
    pass

class HierarchyError(DiscoSuiError):
    """Exception raised for hierarchy-related errors."""
    pass

class TaggingError(DiscoSuiError):
    """Exception raised for tagging-related errors."""
    pass

class SearchError(DiscoSuiError):
    """Exception raised for search-related errors."""
    pass

class TranscriptionError(DiscoSuiError):
    """Exception raised for transcription-related errors."""
    pass

class IndexingError(DiscoSuiError):
    """Exception raised for indexing-related errors."""
    pass

class NoteManagementError(DiscoSuiError):
    """Raised when there's an error in note management operations."""
    pass

class LLMError(DiscoSuiError):
    """Raised when there's an error in LLM operations."""
    pass

class RAGError(DiscoSuiError):
    """Raised when there's an error in RAG operations."""
    pass

class RateLimitError(DiscoSuiError):
    """Raised when rate limit is exceeded."""
    pass

class ResourceNotFoundError(DiscoSuiError):
    """Raised when a requested resource is not found."""
    pass

class PermissionError(DiscoSuiError):
    """Raised when there's a permission error."""
    pass

class NetworkError(DiscoSuiError):
    """Raised when there's a network-related error."""
    pass

class TimeoutError(DiscoSuiError):
    """Raised when an operation times out."""
    pass 