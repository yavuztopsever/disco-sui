from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional, List
from pydantic import Field, validator

class Settings(BaseSettings):
    # Security Settings
    API_KEY: str = Field(..., description="API key for authentication")
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000"],
        description="List of allowed CORS origins"
    )
    RATE_LIMIT_REQUESTS: int = Field(
        default=100,
        description="Number of requests allowed per minute"
    )
    RATE_LIMIT_WINDOW: int = Field(
        default=60,
        description="Time window in seconds for rate limiting"
    )
    
    # Obsidian Vault Settings
    VAULT_PATH: str = Field(..., description="Path to the Obsidian vault")
    AUDIO_FILES_DIR: str = Field(
        default="audio_files",
        description="Directory for storing audio files"
    )
    RAW_EMAILS_DIR: str = Field(
        default="raw_emails",
        description="Directory for storing raw email files"
    )
    PROCESSED_EMAILS_DIR: str = Field(
        default="processed_emails",
        description="Directory for storing processed email files"
    )
    
    # RAG Settings
    RAG_VECTOR_DB_PATH: str = Field(
        default="vector_db",
        description="Path to the vector database"
    )
    RAG_CHUNK_SIZE: int = Field(
        default=1000,
        description="Size of text chunks for RAG"
    )
    RAG_CHUNK_OVERLAP: int = Field(
        default=200,
        description="Overlap between text chunks for RAG"
    )
    RAG_INDEX_UPDATE_INTERVAL: int = Field(
        default=3600,
        description="Interval in seconds between RAG index updates"
    )
    
    # LLM Settings
    OPENAI_API_KEY: str = Field(..., description="OpenAI API key")
    LLM_MODEL: str = Field(
        default="gpt-4",
        description="LLM model to use"
    )
    LLM_TEMPERATURE: float = Field(
        default=0.7,
        description="Temperature for LLM generation",
        ge=0.0,
        le=1.0
    )
    LLM_MAX_TOKENS: int = Field(
        default=2000,
        description="Maximum tokens for LLM generation"
    )
    
    # Server Settings
    HOST: str = Field(
        default="0.0.0.0",
        description="Server host"
    )
    PORT: int = Field(
        default=8000,
        description="Server port",
        ge=1,
        le=65535
    )
    DEBUG: bool = Field(
        default=False,
        description="Enable debug mode"
    )
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level"
    )
    
    # Audio Transcription Settings
    AUDIO_CHECK_INTERVAL_MINUTES: int = Field(
        default=30,
        description="Interval in minutes between audio file checks"
    )
    AUDIO_SUPPORTED_FORMATS: List[str] = Field(
        default=[".mp3", ".wav"],
        description="List of supported audio formats"
    )
    AUDIO_MAX_FILE_SIZE_MB: int = Field(
        default=100,
        description="Maximum audio file size in MB"
    )
    AUDIO_TRANSCRIPTION_MODEL: str = Field(
        default="base",
        description="Whisper model to use for transcription"
    )
    
    # Email Processing Settings
    EMAIL_CHECK_INTERVAL_MINUTES: int = Field(
        default=15,
        description="Interval in minutes between email checks"
    )
    EMAIL_SUPPORTED_FORMATS: List[str] = Field(
        default=[".eml"],
        description="List of supported email formats"
    )
    EMAIL_MAX_FILE_SIZE_MB: int = Field(
        default=50,
        description="Maximum email file size in MB"
    )
    EMAIL_PROCESSING_ENABLED: bool = Field(
        default=True,
        description="Enable email processing"
    )
    EMAIL_ATTACHMENT_STORAGE: str = Field(
        default="attachments",
        description="Directory for storing email attachments"
    )
    
    # Cache Settings
    CACHE_ENABLED: bool = Field(
        default=True,
        description="Enable caching"
    )
    CACHE_TTL: int = Field(
        default=3600,
        description="Cache TTL in seconds"
    )
    
    # Validation
    @validator("ALLOWED_ORIGINS")
    def validate_origins(cls, v):
        if not v:
            raise ValueError("ALLOWED_ORIGINS cannot be empty")
        return v
    
    @validator("RAG_CHUNK_SIZE")
    def validate_chunk_size(cls, v):
        if v < 100:
            raise ValueError("RAG_CHUNK_SIZE must be at least 100")
        return v
    
    @validator("RAG_CHUNK_OVERLAP")
    def validate_chunk_overlap(cls, v, values):
        if "RAG_CHUNK_SIZE" in values and v >= values["RAG_CHUNK_SIZE"]:
            raise ValueError("RAG_CHUNK_OVERLAP must be less than RAG_CHUNK_SIZE")
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings() 