"""Integration tests for backup and recovery flow."""

import pytest
from pathlib import Path
import shutil
from datetime import datetime, timedelta
import json
import yaml
import zipfile

from src.core.config import Settings
from src.services.backup.backup_manager import BackupManager
from src.services.backup.recovery_service import RecoveryService
from src.services.backup.verification_service import BackupVerificationService
from src.core.obsidian_utils import ObsidianUtils

@pytest.fixture
def test_vault(tmp_path) -> Path:
    """Create test vault with sample data."""
    vault_path = tmp_path / "vault"
    vault_path.mkdir()
    
    # Create test vault structure
    content = {
        "notes": {
            "project.md": """---
title: Project Notes
date: 2024-01-15
tags: [project, planning]
---
# Project Planning
Key project details and milestones.""",
            
            "daily/2024-01-17.md": """---
date: 2024-01-17
type: daily
---
# Daily Notes
- Meeting with team
- Project updates
- TODO items""",
            
            "research/data.md": """---
title: Research Data
date: 2024-01-16
tags: [research, data]
---
# Research Findings
Important research data and analysis."""
        },
        
        "attachments": {
            "images/diagram.svg": "<svg>Test diagram content</svg>",
            "documents/spec.pdf": "Test PDF content"
        },
        
        "metadata": {
            "tags.json": """{
                "project": {"count": 2, "related": ["planning"]},
                "research": {"count": 1, "related": ["data"]}
            }""",
            
            "settings.yaml": """
theme: dark
editor:
  font_size: 14
  line_numbers: true
plugins:
  - name: graph_view
    enabled: true
"""
        }
    }
    
    # Create files and directories
    for category, items in content.items():
        category_path = vault_path / category
        category_path.mkdir(parents=True)
        
        for filepath, content in items.items():
            file_path = vault_path / category / filepath
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
    
    return vault_path

@pytest.fixture
def test_environment(tmp_path, test_vault):
    """Set up test environment."""
    # Create necessary directories
    backup_path = tmp_path / "backups"
    backup_path.mkdir()
    recovery_path = tmp_path / "recovery"
    recovery_path.mkdir()
    temp_path = tmp_path / "temp"
    temp_path.mkdir()
    
    return {
        "vault_path": test_vault,
        "backup_path": backup_path,
        "recovery_path": recovery_path,
        "temp_path": temp_path
    }

@pytest.mark.asyncio
async def test_full_backup_creation(test_environment):
    """Test creation of full backup."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        BACKUP_PATH=str(test_environment["backup_path"])
    )
    
    backup_manager = BackupManager()
    await backup_manager.initialize(settings)
    
    # Create full backup
    backup_result = await backup_manager.create_full_backup()
    
    # Verify backup creation
    assert backup_result.success is True
    assert backup_result.backup_path is not None
    assert Path(backup_result.backup_path).exists()
    
    # Verify backup contents
    with zipfile.ZipFile(backup_result.backup_path, 'r') as backup_zip:
        files = backup_zip.namelist()
        assert "notes/project.md" in files
        assert "notes/daily/2024-01-17.md" in files
        assert "metadata/tags.json" in files
        assert "metadata/settings.yaml" in files

@pytest.mark.asyncio
async def test_incremental_backup(test_environment):
    """Test incremental backup functionality."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        BACKUP_PATH=str(test_environment["backup_path"])
    )
    
    backup_manager = BackupManager()
    await backup_manager.initialize(settings)
    
    # Create initial backup
    await backup_manager.create_full_backup()
    
    # Modify vault content
    new_note = test_environment["vault_path"] / "notes/new_note.md"
    new_note.write_text("""---
title: New Note
date: 2024-01-18
---
# New Content""")
    
    # Create incremental backup
    incremental_result = await backup_manager.create_incremental_backup()
    
    # Verify incremental backup
    assert incremental_result.success is True
    assert incremental_result.changes_detected is True
    assert "new_note.md" in incremental_result.backed_up_files

@pytest.mark.asyncio
async def test_backup_verification(test_environment):
    """Test backup verification process."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        BACKUP_PATH=str(test_environment["backup_path"])
    )
    
    backup_manager = BackupManager()
    verification_service = BackupVerificationService()
    
    await backup_manager.initialize(settings)
    await verification_service.initialize(settings)
    
    # Create backup
    backup_result = await backup_manager.create_full_backup()
    
    # Verify backup integrity
    verification_result = await verification_service.verify_backup(
        backup_result.backup_path
    )
    
    # Check verification results
    assert verification_result.success is True
    assert verification_result.integrity_check_passed is True
    assert verification_result.verified_files > 0
    assert len(verification_result.corrupted_files) == 0

@pytest.mark.asyncio
async def test_backup_restoration(test_environment):
    """Test backup restoration process."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        BACKUP_PATH=str(test_environment["backup_path"]),
        RECOVERY_PATH=str(test_environment["recovery_path"])
    )
    
    backup_manager = BackupManager()
    recovery_service = RecoveryService()
    
    await backup_manager.initialize(settings)
    await recovery_service.initialize(settings)
    
    # Create backup
    backup_result = await backup_manager.create_full_backup()
    
    # Perform restoration
    restore_result = await recovery_service.restore_backup(
        backup_result.backup_path,
        test_environment["recovery_path"]
    )
    
    # Verify restoration
    assert restore_result.success is True
    assert restore_result.restored_files > 0
    
    # Compare original and restored content
    original_note = test_environment["vault_path"] / "notes/project.md"
    restored_note = test_environment["recovery_path"] / "notes/project.md"
    assert original_note.read_text() == restored_note.read_text()

@pytest.mark.asyncio
async def test_selective_restoration(test_environment):
    """Test selective backup restoration."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        BACKUP_PATH=str(test_environment["backup_path"]),
        RECOVERY_PATH=str(test_environment["recovery_path"])
    )
    
    backup_manager = BackupManager()
    recovery_service = RecoveryService()
    
    await backup_manager.initialize(settings)
    await recovery_service.initialize(settings)
    
    # Create backup
    backup_result = await backup_manager.create_full_backup()
    
    # Define selective restoration
    restore_paths = ["notes/research", "metadata/tags.json"]
    
    # Perform selective restoration
    restore_result = await recovery_service.restore_selective(
        backup_result.backup_path,
        test_environment["recovery_path"],
        restore_paths
    )
    
    # Verify selective restoration
    assert restore_result.success is True
    assert (test_environment["recovery_path"] / "notes/research/data.md").exists()
    assert (test_environment["recovery_path"] / "metadata/tags.json").exists()
    assert not (test_environment["recovery_path"] / "notes/project.md").exists()

@pytest.mark.asyncio
async def test_backup_scheduling(test_environment):
    """Test backup scheduling functionality."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        BACKUP_PATH=str(test_environment["backup_path"])
    )
    
    backup_manager = BackupManager()
    await backup_manager.initialize(settings)
    
    # Configure backup schedule
    schedule_config = {
        "full_backup": {
            "frequency": "daily",
            "time": "00:00",
            "retention_days": 7
        },
        "incremental_backup": {
            "frequency": "hourly",
            "retention_count": 24
        }
    }
    
    result = await backup_manager.configure_schedule(schedule_config)
    
    # Verify schedule configuration
    assert result.success is True
    assert result.next_full_backup is not None
    assert result.next_incremental_backup is not None

@pytest.mark.asyncio
async def test_backup_retention(test_environment):
    """Test backup retention policies."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        BACKUP_PATH=str(test_environment["backup_path"])
    )
    
    backup_manager = BackupManager()
    await backup_manager.initialize(settings)
    
    # Create multiple backups
    for i in range(5):
        await backup_manager.create_full_backup()
        # Simulate time passage
        backup_manager._current_time = datetime.now() + timedelta(days=i)
    
    # Configure retention policy
    retention_config = {
        "max_backups": 3,
        "max_age_days": 7
    }
    
    result = await backup_manager.apply_retention_policy(retention_config)
    
    # Verify retention
    assert result.success is True
    assert result.retained_backups <= 3
    assert result.removed_backups > 0

@pytest.mark.asyncio
async def test_backup_encryption(test_environment):
    """Test backup encryption and decryption."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        BACKUP_PATH=str(test_environment["backup_path"]),
        RECOVERY_PATH=str(test_environment["recovery_path"])
    )
    
    backup_manager = BackupManager()
    recovery_service = RecoveryService()
    
    await backup_manager.initialize(settings)
    await recovery_service.initialize(settings)
    
    # Configure encryption
    encryption_config = {
        "enabled": True,
        "algorithm": "AES-256",
        "password": "test_password"
    }
    
    # Create encrypted backup
    backup_result = await backup_manager.create_encrypted_backup(encryption_config)
    
    # Verify encryption
    assert backup_result.success is True
    assert backup_result.is_encrypted is True
    
    # Test decryption during restore
    restore_result = await recovery_service.restore_encrypted_backup(
        backup_result.backup_path,
        test_environment["recovery_path"],
        encryption_config
    )
    
    assert restore_result.success is True
    assert restore_result.decryption_successful is True

@pytest.mark.asyncio
async def test_backup_monitoring(test_environment):
    """Test backup monitoring and reporting."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        BACKUP_PATH=str(test_environment["backup_path"])
    )
    
    backup_manager = BackupManager()
    await backup_manager.initialize(settings)
    
    # Register monitoring handler
    backup_events = []
    
    async def monitor_handler(event):
        backup_events.append(event)
    
    await backup_manager.register_monitor_handler(monitor_handler)
    
    # Perform backup operations
    await backup_manager.create_full_backup()
    await backup_manager.create_incremental_backup()
    
    # Generate backup report
    report = await backup_manager.generate_backup_report()
    
    # Verify monitoring
    assert len(backup_events) > 0
    assert report.success is True
    assert report.total_backups > 0
    assert report.last_backup_status == "success" 