"""
Distributed Tracing with OpenTelemetry
"""

import logging
from functools import wraps
from typing import Optional, Callable, Any
from contextlib import asynccontextmanager

from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

from ..config import settings

logger = logging.getLogger(__name__)

# Global tracer
tracer: Optional[trace.Tracer] = None


def setup_tracing(service_name: str = "ios-system"):
    """
    Setup distributed tracing with Jaeger
    
    Usage:
        setup_tracing("ios-api")
    """
    global tracer
    
    # Create resource
    resource = Resource(attributes={
        SERVICE_NAME: service_name,
        "environment": settings.environment,
        "version": settings.version,
    })
    
    # Create tracer provider
    provider = TracerProvider(resource=resource)
    
    # Create Jaeger exporter
    jaeger_exporter = JaegerExporter(
        agent_host_name=settings.jaeger_agent_host,
        agent_port=settings.jaeger_agent_port,
    )
    
    # Add batch span processor
    provider.add_span_processor(
        BatchSpanProcessor(jaeger_exporter)
    )
    
    # Set global tracer provider
    trace.set_tracer_provider(provider)
    
    # Get tracer
    tracer = trace.get_tracer(__name__)
    
    # Auto-instrument libraries
    _auto_instrument()
    
    logger.info(f"Tracing initialized: {service_name} -> {settings.jaeger_agent_host}")
    
    return tracer


def _auto_instrument():
    """Auto-instrument common libraries"""
    
    try:
        # FastAPI
        FastAPIInstrumentor.instrument()
        
        # SQLAlchemy
        SQLAlchemyInstrumentor().instrument()
        
        # Redis
        RedisInstrumentor().instrument()
        
        # HTTP Requests
        RequestsInstrumentor().instrument()
        
        logger.info("Auto-instrumentation complete")
        
    except Exception as e:
        logger.warning(f"Auto-instrumentation failed: {e}")


def trace_async(
    span_name: Optional[str] = None,
    attributes: Optional[dict] = None
):
    """
    Decorator for tracing async functions
    
    Usage:
        @trace_async("process_document")
        async def process_document(file_path: str):
            ...
    """
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not tracer:
                return await func(*args, **kwargs)
            
            # Determine span name
            name = span_name or f"{func.__module__}.{func.__name__}"
            
            # Start span
            with tracer.start_as_current_span(name) as span:
                # Add attributes
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)
                
                # Add function arguments as attributes
                if args:
                    span.set_attribute("args", str(args))
                if kwargs:
                    span.set_attribute("kwargs", str(kwargs))
                
                try:
                    # Execute function
                    result = await func(*args, **kwargs)
                    
                    # Mark success
                    span.set_attribute("success", True)
                    
                    return result
                    
                except Exception as e:
                    # Record exception
                    span.record_exception(e)
                    span.set_attribute("success", False)
                    span.set_attribute("error.type", type(e).__name__)
                    span.set_attribute("error.message", str(e))
                    
                    raise
        
        return wrapper
    return decorator


@asynccontextmanager
async def trace_context(
    span_name: str,
    attributes: Optional[dict] = None
):
    """
    Context manager for tracing code blocks
    
    Usage:
        async with trace_context("database_query", {"query": "SELECT ..."}):
            result = await db.execute(query)
    """
    
    if not tracer:
        yield
        return
    
    with tracer.start_as_current_span(span_name) as span:
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)
        
        try:
            yield span
            span.set_attribute("success", True)
            
        except Exception as e:
            span.record_exception(e)
            span.set_attribute("success", False)
            raise


class TracedClass:
    """
    Base class for auto-tracing all methods
    
    Usage:
        class MyService(TracedClass):
            async def process(self, data):
                # Automatically traced
                ...
    """
    
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        
        # Wrap all async methods
        for attr_name in dir(cls):
            attr = getattr(cls, attr_name)
            
            if (callable(attr) and 
                not attr_name.startswith('_') and
                asyncio.iscoroutinefunction(attr)):
                
                setattr(
                    cls,
                    attr_name,
                    trace_async(f"{cls.__name__}.{attr_name}")(attr)
                )