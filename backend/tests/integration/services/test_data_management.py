"""Integration tests for data management and backup systems."""
import pytest
from pathlib import Path

@pytest.mark.integration
class TestDataManagement:
    """Test suite for data management and backup integration."""
    
    @pytest.mark.asyncio
    async def test_backup_lifecycle(self, initialized_services, validation_helper):
        """Test complete backup lifecycle."""
        backup_manager = initialized_services["backup_manager"]
        
        # 1. Create full backup
        full_backup_result = await backup_manager.create_full_backup()
        await validation_helper(full_backup_result,
                              backup_type="full",
                              files_backed_up=lambda x: x > 0)
        
        # 2. Create incremental backup
        incr_backup_result = await backup_manager.create_incremental_backup()
        await validation_helper(incr_backup_result,
                              backup_type="incremental",
                              parent_backup=full_backup_result.backup_id)
        
        # 3. Verify backups
        verify_result = await backup_manager.verify_backup(
            full_backup_result.backup_path
        )
        await validation_helper(verify_result,
                              integrity_check_passed=True,
                              corrupted_files_count=0)
        
        # 4. List backups
        list_result = await backup_manager.list_backups()
        await validation_helper(list_result,
                              total_backups=2,
                              has_full_backup=True)
        
        # 5. Generate backup report
        report_result = await backup_manager.generate_backup_report()
        await validation_helper(report_result,
                              last_backup_status="success",
                              backup_coverage=lambda x: x > 0)
    
    @pytest.mark.asyncio
    async def test_backup_monitoring(self, initialized_services, validation_helper):
        """Test backup monitoring and event handling."""
        backup_manager = initialized_services["backup_manager"]
        
        # Setup monitoring
        events = []
        async def monitor_handler(event):
            events.append(event)
        
        await backup_manager.register_monitor_handler(monitor_handler)
        
        # Trigger backup operations
        await backup_manager.create_full_backup()
        await backup_manager.create_incremental_backup()
        
        # Verify monitoring
        assert len(events) > 0
        assert any(e["type"] == "backup_started" for e in events)
        assert any(e["type"] == "backup_completed" for e in events)
    
    @pytest.mark.asyncio
    async def test_backup_recovery(self, initialized_services, validation_helper):
        """Test backup recovery scenarios."""
        backup_manager = initialized_services["backup_manager"]
        
        # Create backup
        backup_result = await backup_manager.create_full_backup()
        
        # Simulate data loss
        test_file = Path(backup_result.backup_path) / "test_file.txt"
        test_file.write_text("Test content")
        
        # Recover from backup
        recovery_result = await backup_manager.recover_from_backup(
            backup_result.backup_id,
            [str(test_file)]
        )
        await validation_helper(recovery_result,
                              files_recovered=1,
                              has_errors=False)
    
    @pytest.mark.asyncio
    async def test_data_validation(self, initialized_services, validation_helper):
        """Test data validation and integrity checks."""
        backup_manager = initialized_services["backup_manager"]
        
        # Create test data
        backup_result = await backup_manager.create_full_backup()
        
        # Validate backup data
        validation_result = await backup_manager.validate_backup_data(
            backup_result.backup_id
        )
        await validation_helper(validation_result,
                              valid_files=lambda x: x > 0,
                              validation_errors=[])
        
        # Test incremental validation
        incr_validation = await backup_manager.validate_incremental_changes(
            backup_result.backup_id
        )
        await validation_helper(incr_validation,
                              changes_validated=True)
    
    @pytest.mark.asyncio
    async def test_backup_cleanup(self, initialized_services, validation_helper):
        """Test backup cleanup and maintenance."""
        backup_manager = initialized_services["backup_manager"]
        
        # Create multiple backups
        await backup_manager.create_full_backup()
        await backup_manager.create_incremental_backup()
        await backup_manager.create_incremental_backup()
        
        # Run cleanup
        cleanup_result = await backup_manager.cleanup_old_backups(
            max_age_days=7,
            keep_full_backups=1
        )
        await validation_helper(cleanup_result,
                              backups_removed=lambda x: x >= 0,
                              space_reclaimed=lambda x: x > 0)
        
        # Verify backup state
        state_result = await backup_manager.get_backup_state()
        await validation_helper(state_result,
                              has_valid_full_backup=True,
                              total_size=lambda x: x > 0) 