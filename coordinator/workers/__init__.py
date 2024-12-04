"""
Worker processes for handling agent execution
"""

from typing import Type, Dict
from coordinator.workers.worker import Worker
from coordinator.workers.processor import TaskProcessor

# Worker type registry
WORKER_TYPES: Dict[str, Type[Worker]] = {
    'general': Worker,
    # Add specialized worker types here
}

def get_worker(worker_type: str) -> Type[Worker]:
    """Get worker class by type"""
    if worker_type not in WORKER_TYPES:
        raise ValueError(f"Unknown worker type: {worker_type}")
    return WORKER_TYPES[worker_type]

__all__ = [
    'Worker',
    'TaskProcessor',
    'get_worker',
    'WORKER_TYPES'
]