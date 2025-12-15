# ios_core/profiling.py

import time
import logging
from functools import wraps

logger = logging.getLogger(__name__)


def profile(threshold_ms: float = 100):
    """Profile function execution time"""
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.time()
            
            result = await func(*args, **kwargs)
            
            duration = (time.time() - start) * 1000
            
            if duration > threshold_ms:
                logger.warning(
                    f"SLOW FUNCTION: {func.__name__} took {duration:.2f}ms "
                    f"(threshold: {threshold_ms}ms)"
                )
            
            return result
        
        return wrapper
    return decorator