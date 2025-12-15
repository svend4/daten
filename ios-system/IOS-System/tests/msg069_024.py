"""
Tests for circuit breaker
"""

import pytest
from ios_core.gateway.circuit_breaker import (
    CircuitBreaker, CircuitState, CircuitBreakerOpenError
)


@pytest.fixture
def breaker():
    """Create circuit breaker"""
    return CircuitBreaker(
        name="test",
        failure_threshold=3,
        recovery_timeout=1,
        half_open_max_calls=2
    )


@pytest.mark.asyncio
async def test_circuit_closed_initially(breaker):
    """Test circuit starts in CLOSED state"""
    
    assert breaker.state == CircuitState.CLOSED


@pytest.mark.asyncio
async def test_successful_call(breaker):
    """Test successful call through circuit"""
    
    async def success_func():
        return "success"
    
    result = await breaker.call(success_func)
    
    assert result == "success"
    assert breaker.state == CircuitState.CLOSED
    assert breaker.failure_count == 0


@pytest.mark.asyncio
async def test_failed_call(breaker):
    """Test failed call increases failure count"""
    
    async def fail_func():
        raise Exception("Test error")
    
    with pytest.raises(Exception):
        await breaker.call(fail_func)
    
    assert breaker.failure_count == 1
    assert breaker.state == CircuitState.CLOSED


@pytest.mark.asyncio
async def test_circuit_opens(breaker):
    """Test circuit opens after threshold"""
    
    async def fail_func():
        raise Exception("Test error")
    
    # Fail threshold times
    for _ in range(breaker.failure_threshold):
        with pytest.raises(Exception):
            await breaker.call(fail_func)
    
    # Circuit should be open
    assert breaker.state == CircuitState.OPEN


@pytest.mark.asyncio
async def test_circuit_blocks_when_open(breaker):
    """Test circuit blocks calls when open"""
    
    async def fail_func():
        raise Exception("Test error")
    
    # Open circuit
    for _ in range(breaker.failure_threshold):
        with pytest.raises(Exception):
            await breaker.call(fail_func)
    
    # Next call should be blocked
    with pytest.raises(CircuitBreakerOpenError):
        await breaker.call(fail_func)


@pytest.mark.asyncio
async def test_circuit_recovery(breaker):
    """Test circuit recovery after timeout"""
    
    import asyncio
    
    async def fail_func():
        raise Exception("Test error")
    
    async def success_func():
        return "success"
    
    # Open circuit
    for _ in range(breaker.failure_threshold):
        with pytest.raises(Exception):
            await breaker.call(fail_func)
    
    assert breaker.state == CircuitState.OPEN
    
    # Wait for recovery timeout
    await asyncio.sleep(breaker.recovery_timeout + 0.1)
    
    # Next call should transition to HALF_OPEN
    result = await breaker.call(success_func)
    
    assert result == "success"
    assert breaker.state == CircuitState.HALF_OPEN


@pytest.mark.asyncio
async def test_get_state(breaker):
    """Test getting circuit state"""
    
    state = breaker.get_state()
    
    assert "name" in state
    assert "state" in state
    assert state["name"] == "test"
    assert state["state"] == CircuitState.CLOSED.value