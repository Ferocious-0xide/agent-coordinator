import functools
import logging
import time
import asyncio
from typing import Any, Callable, TypeVar, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

F = TypeVar('F', bound=Callable[..., Any])

def log_execution_time(func: F) -> F:
    """Decorator to log function execution time"""
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.debug(f"{func.__name__} executed in {execution_time:.2f} seconds")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} failed after {execution_time:.2f} seconds: {str(e)}")
            raise

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.debug(f"{func.__name__} executed in {execution_time:.2f} seconds")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} failed after {execution_time:.2f} seconds: {str(e)}")
            raise

    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

def retry_on_failure(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """Decorator to retry function on failure with exponential backoff"""
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            retries = 0
            current_delay = delay
            
            while retries < max_retries:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries == max_retries:
                        logger.error(f"Max retries ({max_retries}) exceeded for {func.__name__}: {str(e)}")
                        raise
                    
                    logger.warning(f"Retry {retries}/{max_retries} for {func.__name__} after {current_delay}s delay")
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            retries = 0
            current_delay = delay
            
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries == max_retries:
                        logger.error(f"Max retries ({max_retries}) exceeded for {func.__name__}: {str(e)}")
                        raise
                    
                    logger.warning(f"Retry {retries}/{max_retries} for {func.__name__} after {current_delay}s delay")
                    time.sleep(current_delay)
                    current_delay *= backoff

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator

def handle_exceptions(func: F) -> F:
    """Decorator to handle and log exceptions"""
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.exception(f"Error in {func.__name__}: {str(e)}")
            raise

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.exception(f"Error in {func.__name__}: {str(e)}")
            raise

    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

def rate_limit(calls: int, period: float):
    """Decorator to rate limit function calls"""
    def decorator(func: F) -> F:
        last_reset = datetime.now()
        calls_made = 0

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            nonlocal last_reset, calls_made
            
            now = datetime.now()
            elapsed = (now - last_reset).total_seconds()
            
            if elapsed > period:
                last_reset = now
                calls_made = 0
            
            if calls_made >= calls:
                sleep_time = period - elapsed
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                    last_reset = datetime.now()
                    calls_made = 0
            
            calls_made += 1
            return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            nonlocal last_reset, calls_made
            
            now = datetime.now()
            elapsed = (now - last_reset).total_seconds()
            
            if elapsed > period:
                last_reset = now
                calls_made = 0
            
            if calls_made >= calls:
                sleep_time = period - elapsed
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    last_reset = datetime.now()
                    calls_made = 0
            
            calls_made += 1
            return func(*args, **kwargs)

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator