"""Core service configuration."""

from typing import List, Dict, Any, Optional
from pathlib import Path
from pydantic import BaseModel, field_validator, ConfigDict
import os
import json


class Settings(BaseModel):
    """Application settings."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    # Server settings
    HOST: str = "localhost"
    PORT: int = 8000
    DEBUG: bool = False
    ALLOWED_ORIGINS: List[str] = ["*"]
    
    # Storage settings
    DATA_DIR: Path = Path("data")
    VAULT_DIR: Path = DATA_DIR / "vault"
    BACKUP_DIR: Path = DATA_DIR / "backups"
    TEMP_DIR: Path = DATA_DIR / "temp"
    LOG_DIR: Path = DATA_DIR / "logs"
    
    # RAG settings
    RAG_CHUNK_SIZE: int = 1000
    RAG_CHUNK_OVERLAP: int = 200
    RAG_MODEL_NAME: str = "sentence-transformers/all-mpnet-base-v2"
    RAG_DEVICE: str = "cpu"
    RAG_BATCH_SIZE: int = 32
    
    # Audio settings
    AUDIO_FILES_DIR: Path = DATA_DIR / "audio"
    AUDIO_SUPPORTED_FORMATS: List[str] = [".mp3", ".wav", ".m4a", ".ogg"]
    
    # Email settings
    RAW_EMAILS_DIR: Path = DATA_DIR / "emails/raw"
    PROCESSED_EMAILS_DIR: Path = DATA_DIR / "emails/processed"
    EMAIL_SUPPORTED_FORMATS: List[str] = [".eml", ".msg"]
    
    # Task settings
    MAX_TASKS_PER_USER: int = 100
    TASK_CLEANUP_DAYS: int = 30
    
    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s [%(levelname)8s] %(message)s (%(filename)s:%(lineno)d)"
    LOG_FILE: Path = LOG_DIR / "app.log"
    
    # Security settings
    SECRET_KEY: str = "your-secret-key"
    TOKEN_EXPIRE_MINUTES: int = 60
    
    @field_validator("ALLOWED_ORIGINS")
    def validate_allowed_origins(cls, v: List[str]) -> List[str]:
        """Validate allowed origins.
        
        Args:
            v: List of allowed origins
            
        Returns:
            Validated list of allowed origins
        """
        if not v:
            return ["*"]
        return v
    
    @field_validator("RAG_CHUNK_OVERLAP")
    def validate_chunk_overlap(cls, v: int) -> int:
        """Validate chunk overlap.
        
        Args:
            v: Chunk overlap value
            
        Returns:
            Validated chunk overlap value
        """
        if v < 0:
            return 0
        if v > 1000:
            return 1000
        return v
    
    @field_validator(
        "AUDIO_FILES_DIR",
        "RAW_EMAILS_DIR",
        "PROCESSED_EMAILS_DIR",
        "DATA_DIR",
        "VAULT_DIR",
        "BACKUP_DIR",
        "TEMP_DIR",
        "LOG_DIR"
    )
    def create_directory(cls, v: Path) -> Path:
        """Create directory if it doesn't exist.
        
        Args:
            v: Directory path
            
        Returns:
            Directory path
        """
        v.mkdir(parents=True, exist_ok=True)
        return v
    
    @field_validator("AUDIO_SUPPORTED_FORMATS", "EMAIL_SUPPORTED_FORMATS")
    def validate_formats(cls, v: List[str]) -> List[str]:
        """Validate file formats.
        
        Args:
            v: List of file formats
            
        Returns:
            Validated list of file formats
        """
        return [fmt.lower() for fmt in v]
    
    def load_from_file(self, file_path: str) -> None:
        """Load settings from a JSON file.
        
        Args:
            file_path: Path to JSON file
        """
        if not os.path.exists(file_path):
            return
            
        with open(file_path, "r") as f:
            data = json.load(f)
            
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def save_to_file(self, file_path: str) -> None:
        """Save settings to a JSON file.
        
        Args:
            file_path: Path to JSON file
        """
        data = self.model_dump()
        
        # Convert Path objects to strings
        for key, value in data.items():
            if isinstance(value, Path):
                data[key] = str(value)
                
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)


# Create global settings instance
settings = Settings()

# Load settings from environment variables
for key in settings.model_fields.keys():
    env_value = os.getenv(key)
    if env_value is not None:
        setattr(settings, key, env_value)

# Load settings from config file
config_file = os.getenv("CONFIG_FILE", "config.json")
if os.path.exists(config_file):
    settings.load_from_file(config_file) 