from typing import Dict, Any, Optional, List
from pathlib import Path
from ...core.base_interfaces import StorageInterface
import shutil
import json
import os

class VaultStorage(StorageInterface):
    """Unified storage service for vault content."""
    name = "vault_storage"
    description = "Manage vault content storage"
    
    def __init__(self, vault_path: Path):
        self.vault_path = vault_path
        self.cache_dir = vault_path / ".cache"
        self.config_dir = vault_path / ".obsidian"
        
    async def initialize(self) -> None:
        """Initialize storage service."""
        # Create necessary directories
        self.cache_dir.mkdir(exist_ok=True)
        self.config_dir.mkdir(exist_ok=True)
        
    async def cleanup(self) -> None:
        """Clean up storage resources."""
        # Clean up temporary files
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
            
    async def read(self, path: Path) -> str:
        """Read content from storage.
        
        Args:
            path: Path to read from
            
        Returns:
            File content
        """
        try:
            full_path = self._resolve_path(path)
            async with open(full_path, 'r', encoding='utf-8') as f:
                return await f.read()
        except Exception as e:
            raise IOError(f"Failed to read {path}: {str(e)}")
            
    async def write(self, path: Path, content: str) -> None:
        """Write content to storage.
        
        Args:
            path: Path to write to
            content: Content to write
        """
        try:
            full_path = self._resolve_path(path)
            full_path.parent.mkdir(parents=True, exist_ok=True)
            async with open(full_path, 'w', encoding='utf-8') as f:
                await f.write(content)
        except Exception as e:
            raise IOError(f"Failed to write to {path}: {str(e)}")
            
    async def delete(self, path: Path) -> None:
        """Delete content from storage.
        
        Args:
            path: Path to delete
        """
        try:
            full_path = self._resolve_path(path)
            if full_path.is_file():
                full_path.unlink()
            elif full_path.is_dir():
                shutil.rmtree(full_path)
        except Exception as e:
            raise IOError(f"Failed to delete {path}: {str(e)}")
            
    async def list_files(
        self,
        directory: Optional[Path] = None,
        pattern: str = "*.md"
    ) -> List[Path]:
        """List files in directory.
        
        Args:
            directory: Directory to list (default: vault root)
            pattern: File pattern to match
            
        Returns:
            List of matching file paths
        """
        directory = self._resolve_path(directory) if directory else self.vault_path
        return list(directory.rglob(pattern))
    
    async def move(self, source: Path, target: Path) -> None:
        """Move content to new location.
        
        Args:
            source: Source path
            target: Target path
        """
        try:
            source_path = self._resolve_path(source)
            target_path = self._resolve_path(target)
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source_path), str(target_path))
        except Exception as e:
            raise IOError(f"Failed to move {source} to {target}: {str(e)}")
    
    async def copy(self, source: Path, target: Path) -> None:
        """Copy content to new location.
        
        Args:
            source: Source path
            target: Target path
        """
        try:
            source_path = self._resolve_path(source)
            target_path = self._resolve_path(target)
            target_path.parent.mkdir(parents=True, exist_ok=True)
            if source_path.is_file():
                shutil.copy2(str(source_path), str(target_path))
            else:
                shutil.copytree(str(source_path), str(target_path))
        except Exception as e:
            raise IOError(f"Failed to copy {source} to {target}: {str(e)}")
    
    def _resolve_path(self, path: Path) -> Path:
        """Resolve full path from relative path.
        
        Args:
            path: Relative path
            
        Returns:
            Full resolved path
        """
        if path.is_absolute():
            if not str(path).startswith(str(self.vault_path)):
                raise ValueError(f"Path {path} is outside vault")
            return path
        return self.vault_path / path 