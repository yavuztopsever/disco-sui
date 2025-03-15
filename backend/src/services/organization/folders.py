"""Folder management functionality."""

from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from ...core.exceptions import FolderNotFoundError

class FolderManager:
    """Manages folder operations in the Obsidian vault."""

    def __init__(self, vault_path: Path):
        """Initialize the folder manager.

        Args:
            vault_path: Path to the Obsidian vault.
        """
        self.vault_path = vault_path

    def create_folder(self, folder_path: str) -> Path:
        """Create a new folder in the vault.

        Args:
            folder_path: Path to the folder relative to the vault root.

        Returns:
            Path to the created folder.
        """
        full_path = self.vault_path / folder_path
        full_path.mkdir(parents=True, exist_ok=True)
        return full_path

    def get_folder(self, folder_path: str) -> Path:
        """Get a folder path.

        Args:
            folder_path: Path to the folder relative to the vault root.

        Returns:
            Path to the folder.

        Raises:
            FolderNotFoundError: If the folder doesn't exist.
        """
        full_path = self.vault_path / folder_path
        if not full_path.exists():
            raise FolderNotFoundError(
                message=f"Folder {folder_path} not found",
                folder_path=folder_path
            )
        return full_path

    def delete_folder(self, folder_path: str, recursive: bool = False) -> bool:
        """Delete a folder.

        Args:
            folder_path: Path to the folder relative to the vault root.
            recursive: Whether to delete non-empty folders.

        Returns:
            True if the folder was deleted, False if it doesn't exist.
        """
        full_path = self.vault_path / folder_path
        if not full_path.exists():
            return False

        if recursive:
            import shutil
            shutil.rmtree(full_path)
        else:
            try:
                full_path.rmdir()
            except OSError:
                return False
        return True

    def list_folders(self, parent_folder: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all folders in a parent folder.

        Args:
            parent_folder: Optional parent folder path relative to the vault root.

        Returns:
            List of dictionaries containing folder information.
        """
        search_path = self.vault_path
        if parent_folder:
            search_path = search_path / parent_folder

        folders = []
        if search_path.exists():
            for folder_path in search_path.glob("**/"):
                if folder_path == search_path:
                    continue
                folders.append({
                    "name": folder_path.name,
                    "path": str(folder_path.relative_to(self.vault_path)),
                    "modified": datetime.fromtimestamp(folder_path.stat().st_mtime).isoformat()
                })
        return folders

    def move_folder(self, source_path: str, target_path: str) -> bool:
        """Move a folder to a new location.

        Args:
            source_path: Current folder path relative to the vault root.
            target_path: New folder path relative to the vault root.

        Returns:
            True if the folder was moved, False if the source doesn't exist.
        """
        source_full_path = self.vault_path / source_path
        target_full_path = self.vault_path / target_path

        if not source_full_path.exists():
            return False

        # Create parent directories if they don't exist
        target_full_path.parent.mkdir(parents=True, exist_ok=True)

        # Move the folder
        source_full_path.rename(target_full_path)
        return True

    def copy_folder(self, source_path: str, target_path: str) -> bool:
        """Copy a folder to a new location.

        Args:
            source_path: Source folder path relative to the vault root.
            target_path: Target folder path relative to the vault root.

        Returns:
            True if the folder was copied, False if the source doesn't exist.
        """
        source_full_path = self.vault_path / source_path
        target_full_path = self.vault_path / target_path

        if not source_full_path.exists():
            return False

        # Create parent directories if they don't exist
        target_full_path.parent.mkdir(parents=True, exist_ok=True)

        # Copy the folder
        import shutil
        shutil.copytree(source_full_path, target_full_path, dirs_exist_ok=True)
        return True 