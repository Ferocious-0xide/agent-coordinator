"""
Core functionality for the coordinator system
"""

from typing import Dict, Any
import asyncio
import logging

logger = logging.getLogger(__name__)

class CoordinatorException(Exception):
    """Base exception for coordinator errors"""
    pass

class TaskQueueException(CoordinatorException):
    """Raised when task queue operations fail"""
    pass

class StateException(CoordinatorException):
    """Raised when state operations fail"""
    pass

# Export exception classes
__all__ = [
    'CoordinatorException',
    'TaskQueueException',
    'StateException'
]