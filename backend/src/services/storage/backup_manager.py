import os
import shutil
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

class BackupManager:
    """Manages backups of Obsidian vaults."""
    
    def __init__(self, backup_dir: str):
        """Initialize backup manager.
        
        Args:
            backup_dir: Directory to store backups
        """
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
    def create_backup(self, vault_path: str, name: Optional[str] = None) -> str:
        """Create a backup of the vault.
        
        Args:
            vault_path: Path to vault to backup
            name: Optional name for the backup
            
        Returns:
            Path to created backup
            
        Raises:
            OSError: If backup creation fails
        """
        vault_path = Path(vault_path)
        if not vault_path.exists():
            raise OSError(f"Vault path does not exist: {vault_path}")
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = name or f"backup_{timestamp}"
        backup_path = self.backup_dir / backup_name
        
        try:
            shutil.copytree(vault_path, backup_path)
            logger.info(f"Created backup at {backup_path}")
            return str(backup_path)
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            raise OSError(f"Backup creation failed: {e}")
            
    def restore_backup(self, backup_name: str, target_path: str) -> None:
        """Restore a backup to target location.
        
        Args:
            backup_name: Name of backup to restore
            target_path: Path to restore backup to
            
        Raises:
            OSError: If backup restoration fails
        """
        backup_path = self.backup_dir / backup_name
        target_path = Path(target_path)
        
        if not backup_path.exists():
            raise OSError(f"Backup does not exist: {backup_path}")
            
        try:
            if target_path.exists():
                shutil.rmtree(target_path)
            shutil.copytree(backup_path, target_path)
            logger.info(f"Restored backup to {target_path}")
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            raise OSError(f"Backup restoration failed: {e}")
            
    def list_backups(self) -> List[str]:
        """List available backups.
        
        Returns:
            List of backup names
        """
        return [d.name for d in self.backup_dir.iterdir() if d.is_dir()]
        
    def delete_backup(self, backup_name: str) -> None:
        """Delete a backup.
        
        Args:
            backup_name: Name of backup to delete
            
        Raises:
            OSError: If backup deletion fails
        """
        backup_path = self.backup_dir / backup_name
        
        if not backup_path.exists():
            raise OSError(f"Backup does not exist: {backup_path}")
            
        try:
            shutil.rmtree(backup_path)
            logger.info(f"Deleted backup {backup_name}")
        except Exception as e:
            logger.error(f"Failed to delete backup: {e}")
            raise OSError(f"Backup deletion failed: {e}")
            
    def cleanup_old_backups(self, max_backups: int) -> None:
        """Remove oldest backups exceeding maximum count.
        
        Args:
            max_backups: Maximum number of backups to keep
        """
        backups = sorted(
            [(d.name, d.stat().st_mtime) for d in self.backup_dir.iterdir() if d.is_dir()],
            key=lambda x: x[1]
        )
        
        while len(backups) > max_backups:
            oldest = backups.pop(0)[0]
            try:
                self.delete_backup(oldest)
            except OSError as e:
                logger.warning(f"Failed to delete old backup {oldest}: {e}") 