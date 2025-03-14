from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional, List, Dict, Any, Union
from pydantic import Field, validator, DirectoryPath, FilePath, constr, conint, confloat
import os
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class LogLevel(str, Enum):
    """Valid logging levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class LLMModel(str, Enum):
    """Supported LLM models."""
    GPT4 = "gpt-4"
    GPT4_TURBO = "gpt-4-turbo-preview"
    GPT35_TURBO = "gpt-3.5-turbo"

class WhisperModel(str, Enum):
    """Supported Whisper models."""
    TINY = "tiny"
    BASE = "base"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"

class VectorDBType(str, Enum):
    """Supported vector database types."""
    CHROMA = "chroma"
    FAISS = "faiss"
    PINECONE = "pinecone"

class Settings(BaseSettings):
    """Application configuration settings.
    
    This class uses Pydantic for configuration management and validation.
    Settings can be loaded from environment variables or a .env file.
    """
    
    # Security Settings
    API_KEY: str = Field(
        ...,
        description="API key for authentication",
        min_length=32
    )
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000"],
        description="List of allowed CORS origins"
    )
    RATE_LIMIT_REQUESTS: conint(gt=0) = Field(
        default=100,
        description="Number of requests allowed per minute"
    )
    RATE_LIMIT_WINDOW: conint(gt=0) = Field(
        default=60,
        description="Time window in seconds for rate limiting"
    )
    JWT_SECRET: str = Field(
        ...,
        description="Secret key for JWT token generation",
        min_length=32
    )
    JWT_EXPIRATION: conint(gt=0) = Field(
        default=3600,
        description="JWT token expiration time in seconds"
    )
    
    # Obsidian Vault Settings
    VAULT_PATH: DirectoryPath = Field(
        ...,
        description="Path to the Obsidian vault"
    )
    AUDIO_FILES_DIR: DirectoryPath = Field(
        default=Path("audio_files"),
        description="Directory for storing audio files"
    )
    RAW_EMAILS_DIR: DirectoryPath = Field(
        default=Path("raw_emails"),
        description="Directory for storing raw email files"
    )
    PROCESSED_EMAILS_DIR: DirectoryPath = Field(
        default=Path("processed_emails"),
        description="Directory for storing processed email files"
    )
    TEMPLATE_DIR: DirectoryPath = Field(
        default=Path("templates"),
        description="Directory containing note templates"
    )
    
    # RAG Settings
    VECTOR_DB_TYPE: VectorDBType = Field(
        default=VectorDBType.CHROMA,
        description="Type of vector database to use"
    )
    RAG_VECTOR_DB_PATH: DirectoryPath = Field(
        default=Path("vector_db"),
        description="Path to the vector database"
    )
    RAG_CHUNK_SIZE: conint(gt=100) = Field(
        default=1000,
        description="Size of text chunks for RAG"
    )
    RAG_CHUNK_OVERLAP: conint(gt=0) = Field(
        default=200,
        description="Overlap between text chunks for RAG"
    )
    RAG_INDEX_UPDATE_INTERVAL: conint(gt=0) = Field(
        default=3600,
        description="Interval in seconds between RAG index updates"
    )
    RAG_SIMILARITY_THRESHOLD: confloat(gt=0.0, lt=1.0) = Field(
        default=0.7,
        description="Minimum similarity score for RAG results"
    )
    RAG_MAX_RESULTS: conint(gt=0) = Field(
        default=5,
        description="Maximum number of results to return from RAG queries"
    )
    
    # LLM Settings
    OPENAI_API_KEY: str = Field(
        ...,
        description="OpenAI API key",
        min_length=32
    )
    LLM_MODEL: LLMModel = Field(
        default=LLMModel.GPT4,
        description="LLM model to use"
    )
    LLM_TEMPERATURE: confloat(ge=0.0, le=1.0) = Field(
        default=0.7,
        description="Temperature for LLM generation"
    )
    LLM_MAX_TOKENS: conint(gt=0) = Field(
        default=2000,
        description="Maximum tokens for LLM generation"
    )
    LLM_TIMEOUT: conint(gt=0) = Field(
        default=30,
        description="Timeout in seconds for LLM requests"
    )
    LLM_RETRY_ATTEMPTS: conint(ge=0) = Field(
        default=3,
        description="Number of retry attempts for failed LLM requests"
    )
    LLM_RETRY_DELAY: conint(gt=0) = Field(
        default=1,
        description="Delay in seconds between retry attempts"
    )
    
    # Server Settings
    HOST: str = Field(
        default="0.0.0.0",
        description="Server host"
    )
    PORT: conint(gt=0, lt=65536) = Field(
        default=8000,
        description="Server port"
    )
    DEBUG: bool = Field(
        default=False,
        description="Enable debug mode"
    )
    LOG_LEVEL: LogLevel = Field(
        default=LogLevel.INFO,
        description="Logging level"
    )
    WORKERS: conint(gt=0) = Field(
        default=4,
        description="Number of worker processes"
    )
    
    # Audio Transcription Settings
    AUDIO_CHECK_INTERVAL_MINUTES: conint(gt=0) = Field(
        default=30,
        description="Interval in minutes between audio file checks"
    )
    AUDIO_SUPPORTED_FORMATS: List[str] = Field(
        default=[".mp3", ".wav", ".m4a", ".ogg"],
        description="List of supported audio formats"
    )
    AUDIO_MAX_FILE_SIZE_MB: conint(gt=0) = Field(
        default=100,
        description="Maximum audio file size in MB"
    )
    AUDIO_TRANSCRIPTION_MODEL: WhisperModel = Field(
        default=WhisperModel.BASE,
        description="Whisper model to use for transcription"
    )
    AUDIO_BATCH_SIZE: conint(gt=0) = Field(
        default=10,
        description="Number of audio files to process in one batch"
    )
    
    # Email Processing Settings
    EMAIL_CHECK_INTERVAL_MINUTES: conint(gt=0) = Field(
        default=15,
        description="Interval in minutes between email checks"
    )
    EMAIL_SUPPORTED_FORMATS: List[str] = Field(
        default=[".eml", ".msg"],
        description="List of supported email formats"
    )
    EMAIL_MAX_FILE_SIZE_MB: conint(gt=0) = Field(
        default=50,
        description="Maximum email file size in MB"
    )
    EMAIL_PROCESSING_ENABLED: bool = Field(
        default=True,
        description="Enable email processing"
    )
    EMAIL_ATTACHMENT_STORAGE: DirectoryPath = Field(
        default=Path("attachments"),
        description="Directory for storing email attachments"
    )
    EMAIL_BATCH_SIZE: conint(gt=0) = Field(
        default=20,
        description="Number of emails to process in one batch"
    )
    
    # Cache Settings
    CACHE_ENABLED: bool = Field(
        default=True,
        description="Enable caching"
    )
    CACHE_TTL: conint(gt=0) = Field(
        default=3600,
        description="Cache TTL in seconds"
    )
    CACHE_MAX_SIZE_MB: conint(gt=0) = Field(
        default=1000,
        description="Maximum cache size in MB"
    )
    CACHE_CLEANUP_INTERVAL: conint(gt=0) = Field(
        default=300,
        description="Cache cleanup interval in seconds"
    )
    
    # Note Template Settings
    TEMPLATE_ENFORCE_STRICT: bool = Field(
        default=True,
        description="Strictly enforce note templates"
    )
    TEMPLATE_AUTO_UPDATE: bool = Field(
        default=True,
        description="Automatically update notes when templates change"
    )
    TEMPLATE_CHECK_INTERVAL: conint(gt=0) = Field(
        default=3600,
        description="Interval in seconds between template compliance checks"
    )
    
    # Validation
    @validator("ALLOWED_ORIGINS")
    def validate_origins(cls, v):
        """Validate allowed origins."""
        if not v:
            raise ValueError("ALLOWED_ORIGINS cannot be empty")
        return v
    
    @validator("RAG_CHUNK_OVERLAP")
    def validate_chunk_overlap(cls, v, values):
        """Validate chunk overlap is less than chunk size."""
        if "RAG_CHUNK_SIZE" in values and v >= values["RAG_CHUNK_SIZE"]:
            raise ValueError("RAG_CHUNK_OVERLAP must be less than RAG_CHUNK_SIZE")
        return v
    
    @validator("AUDIO_FILES_DIR", "RAW_EMAILS_DIR", "PROCESSED_EMAILS_DIR", 
              "EMAIL_ATTACHMENT_STORAGE", "TEMPLATE_DIR", "RAG_VECTOR_DB_PATH")
    def create_directory(cls, v):
        """Create directory if it doesn't exist."""
        os.makedirs(v, exist_ok=True)
        return v
    
    @validator("AUDIO_SUPPORTED_FORMATS", "EMAIL_SUPPORTED_FORMATS")
    def validate_formats(cls, v):
        """Validate file format extensions."""
        if not all(x.startswith(".") for x in v):
            raise ValueError("File format extensions must start with '.'")
        return v
    
    def get_vector_db_config(self) -> Dict[str, Any]:
        """Get vector database configuration.
        
        Returns:
            Dict[str, Any]: Vector database configuration
        """
        return {
            "type": self.VECTOR_DB_TYPE,
            "path": self.RAG_VECTOR_DB_PATH,
            "similarity_threshold": self.RAG_SIMILARITY_THRESHOLD,
            "max_results": self.RAG_MAX_RESULTS
        }
    
    def get_llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration.
        
        Returns:
            Dict[str, Any]: LLM configuration
        """
        return {
            "model": self.LLM_MODEL,
            "temperature": self.LLM_TEMPERATURE,
            "max_tokens": self.LLM_MAX_TOKENS,
            "timeout": self.LLM_TIMEOUT,
            "retry_attempts": self.LLM_RETRY_ATTEMPTS,
            "retry_delay": self.LLM_RETRY_DELAY
        }
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        case_sensitive = True
        validate_assignment = True
        extra = "forbid"

# Initialize settings
try:
    settings = Settings()
    logger.info("Configuration loaded successfully")
except Exception as e:
    logger.error(f"Failed to load configuration: {e}")
    raise 