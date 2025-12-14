"""
Tests for MFA
"""

import pytest
import pyotp

from ios_core.security.mfa import mfa_manager


@pytest.mark.asyncio
async def test_setup_mfa():
    """Test MFA setup"""
    
    result = await mfa_manager.setup_mfa(
        user_id="test_user",
        user_email="test@example.com"
    )
    
    assert "qr_code" in result
    assert "secret" in result
    assert "backup_codes" in result
    assert len(result["backup_codes"]) == 10


@pytest.mark.asyncio
async def test_verify_code():
    """Test TOTP code verification"""
    
    # Setup MFA
    result = await mfa_manager.setup_mfa(
        user_id="test_user",
        user_email="test@example.com"
    )
    
    secret = result["secret"]
    
    # Generate valid code
    totp = pyotp.TOTP(secret)
    valid_code = totp.now()
    
    # Verify
    is_valid = await mfa_manager.verify_code("test_user", valid_code)
    
    assert is_valid


@pytest.mark.asyncio
async def test_verify_backup_code():
    """Test backup code verification"""
    
    # Setup MFA
    result = await mfa_manager.setup_mfa(
        user_id="test_user",
        user_email="test@example.com"
    )
    
    backup_code = result["backup_codes"][0]
    
    # Verify backup code
    is_valid = await mfa_manager.verify_code("test_user", backup_code)
    
    assert is_valid
    
    # Should not work twice
    is_valid = await mfa_manager.verify_code("test_user", backup_code)
    
    assert not is_valid


@pytest.mark.asyncio
async def test_enable_disable_mfa():
    """Test enable/disable MFA"""
    
    user_id = "test_user"
    
    # Setup
    await mfa_manager.setup_mfa(user_id, "test@example.com")
    
    # Not enabled yet
    assert not await mfa_manager.is_enabled(user_id)
    
    # Enable
    await mfa_manager.enable_mfa(user_id)
    
    assert await mfa_manager.is_enabled(user_id)
    
    # Disable
    await mfa_manager.disable_mfa(user_id)
    
    assert not await mfa_manager.is_enabled(user_id)