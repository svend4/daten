"""
Tests for distributed tracing
"""

import pytest
from unittest.mock import Mock, patch

from ios_core.observability.tracing import (
    setup_tracing,
    trace_async,
    trace_context
)


def test_setup_tracing():
    """Test tracing setup"""
    
    tracer = setup_tracing("test-service")
    
    assert tracer is not None


@pytest.mark.asyncio
async def test_trace_async_decorator():
    """Test async tracing decorator"""
    
    setup_tracing("test")
    
    @trace_async("test_function")
    async def test_func(x: int) -> int:
        return x * 2
    
    result = await test_func(5)
    
    assert result == 10


@pytest.mark.asyncio
async def test_trace_async_with_exception():
    """Test tracing with exception"""
    
    setup_tracing("test")
    
    @trace_async("test_error")
    async def test_func():
        raise ValueError("Test error")
    
    with pytest.raises(ValueError):
        await test_func()


@pytest.mark.asyncio
async def test_trace_context():
    """Test trace context manager"""
    
    setup_tracing("test")
    
    async with trace_context("test_context", {"key": "value"}):
        # Code is traced
        pass