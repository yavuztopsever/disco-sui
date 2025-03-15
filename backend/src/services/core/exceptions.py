"""Core service exceptions."""

class ServiceError(Exception):
    """Base class for service-related exceptions."""
    pass

class AnalysisError(ServiceError):
    """Exception raised when analysis operations fail."""
    pass

class ReorganizationError(ServiceError):
    """Exception raised when reorganization operations fail."""
    pass

class IndexingError(ServiceError):
    """Exception raised when indexing operations fail."""
    pass

class StorageError(ServiceError):
    """Exception raised when storage operations fail."""
    pass

class NoteError(ServiceError):
    """Exception raised when note operations fail."""
    pass

class NoteNotFoundError(NoteError):
    """Exception raised when a note is not found."""
    pass

class NoteExistsError(NoteError):
    """Exception raised when attempting to create a note that already exists."""
    pass

class NoteValidationError(NoteError):
    """Exception raised when note validation fails."""
    pass

class NoteContentError(NoteError):
    """Exception raised when note content is invalid."""
    pass

class NoteMetadataError(NoteError):
    """Exception raised when note metadata is invalid."""
    pass

class NoteLinkError(NoteError):
    """Exception raised when note link operations fail."""
    pass

class NoteTagError(NoteError):
    """Exception raised when note tag operations fail."""
    pass

class NoteAlreadyExistsError(NoteError):
    """Exception raised when attempting to create a note that already exists."""
    pass

class TemplateError(ServiceError):
    """Exception raised when template operations fail."""
    pass

class ValidationError(ServiceError):
    """Exception raised when validation fails."""
    pass

class ConfigurationError(ServiceError):
    """Exception raised when configuration is invalid."""
    pass

class AuthenticationError(ServiceError):
    """Exception raised when authentication fails."""
    pass

class AuthorizationError(ServiceError):
    """Exception raised when authorization fails."""
    pass

class NetworkError(ServiceError):
    """Exception raised when network operations fail."""
    pass

class ResourceNotFoundError(ServiceError):
    """Exception raised when a requested resource is not found."""
    pass

class ResourceExistsError(ServiceError):
    """Exception raised when attempting to create a resource that already exists."""
    pass

class InvalidOperationError(ServiceError):
    """Exception raised when an operation is invalid in the current context."""
    pass

class DependencyError(ServiceError):
    """Exception raised when a required dependency is missing or invalid."""
    pass

class TimeoutError(ServiceError):
    """Exception raised when an operation times out."""
    pass

class ConcurrencyError(ServiceError):
    """Exception raised when concurrent operations conflict."""
    pass

class RAGError(ServiceError):
    pass 