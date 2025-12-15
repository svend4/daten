"""
Structured Logging with JSON output
"""

import logging
import json
import sys
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

from pythonjsonlogger import jsonlogger

from ..config import settings


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields"""
    
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        
        # Add timestamp in ISO format
        log_record['timestamp'] = datetime.utcnow().isoformat()
        
        # Add service name
        log_record['service'] = settings.service_name
        
        # Add environment
        log_record['environment'] = settings.environment
        
        # Add version
        log_record['version'] = settings.version
        
        # Add trace context if available
        from opentelemetry import trace
        span = trace.get_current_span()
        if span:
            context = span.get_span_context()
            log_record['trace_id'] = format(context.trace_id, '032x')
            log_record['span_id'] = format(context.span_id, '016x')
        
        # Rename level to match ELK convention
        if 'levelname' in log_record:
            log_record['level'] = log_record.pop('levelname')


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[Path] = None,
    json_format: bool = True
):
    """
    Setup structured logging
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for file logging
        json_format: Use JSON format (for ELK)
    """
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    
    if json_format:
        # JSON formatter for structured logging
        formatter = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s'
        )
    else:
        # Standard formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Set levels for noisy libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    
    logging.info(
        "Logging configured",
        extra={
            'log_level': log_level,
            'json_format': json_format,
            'log_file': str(log_file) if log_file else None
        }
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get logger with name
    
    Usage:
        logger = get_logger(__name__)
        logger.info("Message", extra={'key': 'value'})
    """
    return logging.getLogger(name)


class StructuredLogger:
    """
    Wrapper for structured logging with context
    
    Usage:
        logger = StructuredLogger(__name__)
        logger.info("User logged in", user_id=123, ip="1.2.3.4")
    """
    
    def __init__(self, name: str, context: Optional[Dict[str, Any]] = None):
        self.logger = logging.getLogger(name)
        self.context = context or {}
    
    def _log(self, level: int, message: str, **kwargs):
        """Log with context"""
        extra = {**self.context, **kwargs}
        self.logger.log(level, message, extra=extra)
    
    def debug(self, message: str, **kwargs):
        self._log(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        self._log(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        self._log(logging.CRITICAL, message, **kwargs)
    
    def exception(self, message: str, **kwargs):
        """Log exception with traceback"""
        self.logger.exception(message, extra={**self.context, **kwargs})
    
    def with_context(self, **context) -> 'StructuredLogger':
        """Create new logger with additional context"""
        return StructuredLogger(
            self.logger.name,
            {**self.context, **context}
        )