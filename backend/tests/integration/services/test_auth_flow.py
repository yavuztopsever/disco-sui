"""Integration tests for authentication and authorization flow."""

import pytest
from pathlib import Path
import shutil
from datetime import datetime, timedelta
import jwt
import bcrypt

from src.core.config import Settings
from src.services.auth.auth_manager import AuthManager
from src.services.auth.token_service import TokenService
from src.services.auth.permission_manager import PermissionManager
from src.core.obsidian_utils import ObsidianUtils

@pytest.fixture
def test_users():
    """Create test user data."""
    # Create hashed passwords
    password_hash = bcrypt.hashpw("test_password".encode(), bcrypt.gensalt())
    admin_hash = bcrypt.hashpw("admin_password".encode(), bcrypt.gensalt())
    
    return {
        "regular_user": {
            "username": "test_user",
            "password_hash": password_hash,
            "email": "test@example.com",
            "roles": ["user"],
            "permissions": ["read", "write"]
        },
        "admin_user": {
            "username": "admin_user",
            "password_hash": admin_hash,
            "email": "admin@example.com",
            "roles": ["admin", "user"],
            "permissions": ["read", "write", "admin"]
        }
    }

@pytest.fixture
def test_environment(tmp_path, test_users):
    """Set up test environment."""
    # Create necessary directories
    auth_path = tmp_path / "auth"
    auth_path.mkdir()
    token_path = tmp_path / "tokens"
    token_path.mkdir()
    
    # Create user database file
    user_db = auth_path / "users.json"
    user_db.write_text(str(test_users))
    
    return {
        "auth_path": auth_path,
        "token_path": token_path,
        "user_db": user_db
    }

@pytest.mark.asyncio
async def test_user_authentication(test_environment):
    """Test user authentication process."""
    # Initialize services
    settings = Settings(
        AUTH_PATH=str(test_environment["auth_path"]),
        TOKEN_PATH=str(test_environment["token_path"])
    )
    
    auth_manager = AuthManager()
    await auth_manager.initialize(settings)
    
    # Test successful authentication
    auth_result = await auth_manager.authenticate(
        username="test_user",
        password="test_password"
    )
    
    # Verify successful authentication
    assert auth_result.success is True
    assert auth_result.user is not None
    assert auth_result.token is not None
    
    # Test failed authentication
    failed_result = await auth_manager.authenticate(
        username="test_user",
        password="wrong_password"
    )
    
    # Verify failed authentication
    assert failed_result.success is False
    assert failed_result.error_message is not None

@pytest.mark.asyncio
async def test_token_management(test_environment):
    """Test token generation and validation."""
    # Initialize services
    settings = Settings(
        TOKEN_PATH=str(test_environment["token_path"])
    )
    
    token_service = TokenService()
    await token_service.initialize(settings)
    
    # Generate token
    user_data = {
        "username": "test_user",
        "roles": ["user"],
        "permissions": ["read", "write"]
    }
    
    token_result = await token_service.generate_token(user_data)
    
    # Verify token generation
    assert token_result.success is True
    assert token_result.token is not None
    
    # Validate token
    validation_result = await token_service.validate_token(token_result.token)
    
    # Verify token validation
    assert validation_result.success is True
    assert validation_result.user_data["username"] == "test_user"
    assert "user" in validation_result.user_data["roles"]

@pytest.mark.asyncio
async def test_permission_management(test_environment):
    """Test permission management and role-based access control."""
    # Initialize services
    settings = Settings(
        AUTH_PATH=str(test_environment["auth_path"])
    )
    
    permission_manager = PermissionManager()
    await permission_manager.initialize(settings)
    
    # Test permission checking
    admin_check = await permission_manager.check_permission(
        username="admin_user",
        permission="admin"
    )
    
    user_check = await permission_manager.check_permission(
        username="test_user",
        permission="admin"
    )
    
    # Verify permission checks
    assert admin_check.has_permission is True
    assert user_check.has_permission is False

@pytest.mark.asyncio
async def test_session_management(test_environment):
    """Test user session management."""
    # Initialize services
    settings = Settings(
        AUTH_PATH=str(test_environment["auth_path"]),
        TOKEN_PATH=str(test_environment["token_path"])
    )
    
    auth_manager = AuthManager()
    await auth_manager.initialize(settings)
    
    # Create session
    session_result = await auth_manager.create_session("test_user")
    
    # Verify session creation
    assert session_result.success is True
    assert session_result.session_id is not None
    
    # Validate session
    validation_result = await auth_manager.validate_session(session_result.session_id)
    assert validation_result.success is True
    assert validation_result.is_valid is True
    
    # Expire session
    expiry_result = await auth_manager.expire_session(session_result.session_id)
    assert expiry_result.success is True
    
    # Verify expired session
    expired_validation = await auth_manager.validate_session(session_result.session_id)
    assert expired_validation.is_valid is False

@pytest.mark.asyncio
async def test_role_management(test_environment):
    """Test role management and hierarchy."""
    # Initialize services
    settings = Settings(
        AUTH_PATH=str(test_environment["auth_path"])
    )
    
    permission_manager = PermissionManager()
    await permission_manager.initialize(settings)
    
    # Define role hierarchy
    roles = {
        "admin": ["user", "moderator"],
        "moderator": ["user"],
        "user": []
    }
    
    # Set up role hierarchy
    hierarchy_result = await permission_manager.set_role_hierarchy(roles)
    
    # Verify role hierarchy
    assert hierarchy_result.success is True
    
    # Test role inheritance
    admin_perms = await permission_manager.get_role_permissions("admin")
    mod_perms = await permission_manager.get_role_permissions("moderator")
    
    assert all(perm in admin_perms.permissions for perm in mod_perms.permissions)

@pytest.mark.asyncio
async def test_security_features(test_environment):
    """Test security features and protections."""
    # Initialize services
    settings = Settings(
        AUTH_PATH=str(test_environment["auth_path"]),
        TOKEN_PATH=str(test_environment["token_path"])
    )
    
    auth_manager = AuthManager()
    await auth_manager.initialize(settings)
    
    # Test brute force protection
    failed_attempts = []
    for _ in range(5):
        result = await auth_manager.authenticate(
            username="test_user",
            password="wrong_password"
        )
        failed_attempts.append(result)
    
    # Verify account lockout
    lockout_check = await auth_manager.check_account_status("test_user")
    assert lockout_check.is_locked is True
    assert lockout_check.lockout_expiry is not None
    
    # Test password complexity
    password_check = await auth_manager.check_password_strength("weak")
    assert password_check.is_strong is False
    assert len(password_check.requirements) > 0

@pytest.mark.asyncio
async def test_audit_logging(test_environment):
    """Test authentication audit logging."""
    # Initialize services
    settings = Settings(
        AUTH_PATH=str(test_environment["auth_path"]),
        TOKEN_PATH=str(test_environment["token_path"])
    )
    
    auth_manager = AuthManager()
    await auth_manager.initialize(settings)
    
    # Perform various authentication actions
    await auth_manager.authenticate("test_user", "test_password")
    await auth_manager.authenticate("test_user", "wrong_password")
    
    # Generate audit log
    audit_result = await auth_manager.generate_audit_log()
    
    # Verify audit logging
    assert audit_result.success is True
    assert len(audit_result.log_entries) >= 2
    assert any(entry.action == "login_success" for entry in audit_result.log_entries)
    assert any(entry.action == "login_failure" for entry in audit_result.log_entries) 