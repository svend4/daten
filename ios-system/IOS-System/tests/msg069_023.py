"""
Tests for rate limiter
"""

import pytest
import asyncio
from ios_core.gateway.rate_limiter import rate_limiter, RateLimitTier


@pytest.fixture
async def limiter():
    """Initialize rate limiter"""
    await rate_limiter.initialize()
    yield rate_limiter
    # Cleanup
    await rate_limiter.reset("test:user")


@pytest.mark.asyncio
async def test_rate_limit_basic(limiter):
    """Test basic rate limiting"""
    
    key = "test:user"
    
    # First request should pass
    allowed, retry_after = await limiter.check_rate_limit(
        key=key,
        tier=RateLimitTier.FREE
    )
    
    assert allowed is True
    assert retry_after is None


@pytest.mark.asyncio
async def test_rate_limit_exceeded(limiter):
    """Test rate limit exceeded"""
    
    key = "test:user_heavy"
    tier = RateLimitTier.FREE
    
    # Get limit for second window
    limit = limiter.TIER_LIMITS[tier]["second"]
    
    # Make requests up to limit
    for i in range(limit):
        allowed, _ = await limiter.check_rate_limit(key=key, tier=tier)
        assert allowed is True, f"Request {i+1}/{limit} should be allowed"
    
    # Next request should fail
    allowed, retry_after = await limiter.check_rate_limit(key=key, tier=tier)
    
    assert allowed is False
    assert retry_after is not None
    assert retry_after > 0


@pytest.mark.asyncio
async def test_tier_differences(limiter):
    """Test different tier limits"""
    
    free_limit = limiter.TIER_LIMITS[RateLimitTier.FREE]["minute"]
    premium_limit = limiter.TIER_LIMITS[RateLimitTier.PREMIUM]["minute"]
    
    assert premium_limit > free_limit


@pytest.mark.asyncio
async def test_get_usage(limiter):
    """Test getting usage statistics"""
    
    key = "test:user_usage"
    tier = RateLimitTier.FREE
    
    # Make some requests
    for _ in range(3):
        await limiter.check_rate_limit(key=key, tier=tier)
    
    # Get usage
    usage = await limiter.get_usage(key=key, tier=tier)
    
    assert "second" in usage
    assert "minute" in usage
    assert usage["second"]["used"] >= 3
    assert usage["second"]["limit"] > 0


@pytest.mark.asyncio
async def test_reset(limiter):
    """Test resetting rate limits"""
    
    key = "test:user_reset"
    tier = RateLimitTier.FREE
    
    # Use up some quota
    for _ in range(5):
        await limiter.check_rate_limit(key=key, tier=tier)
    
    # Reset
    await limiter.reset(key)
    
    # Usage should be cleared
    usage = await limiter.get_usage(key=key, tier=tier)
    assert usage["second"]["used"] == 0