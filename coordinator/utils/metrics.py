import time
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from prometheus_client import Counter, Gauge, Histogram, Summary

logger = logging.getLogger(__name__)

# System Metrics
SYSTEM_MEMORY = Gauge('system_memory_usage_bytes', 'System memory usage in bytes')
SYSTEM_CPU = Gauge('system_cpu_usage_percent', 'System CPU usage percentage')
SYSTEM_DISK = Gauge('system_disk_usage_percent', 'System disk usage percentage')

# Worker Metrics
WORKER_COUNT = Gauge('worker_count', 'Number of active workers')
WORKER_TASKS = Counter('worker_tasks_total', 'Total tasks processed by workers', ['worker_id', 'status'])
WORKER_PROCESSING_TIME = Histogram(
    'worker_processing_seconds', 
    'Time spent processing tasks',
    ['worker_id']
)

# Agent Metrics
AGENT_COUNT = Gauge('agent_count', 'Number of active agents')
AGENT_TASKS = Counter('agent_tasks_total', 'Total tasks processed by agents', ['agent_id', 'type'])
AGENT_ERRORS = Counter('agent_errors_total', 'Total agent errors', ['agent_id', 'type'])
AGENT_PROCESSING_TIME = Histogram(
    'agent_processing_seconds',
    'Time spent processing tasks by agents',
    ['agent_id', 'type']
)

# Task Metrics
TASK_STATUS = Counter('task_status_total', 'Task status counts', ['status'])
TASK_QUEUE_SIZE = Gauge('task_queue_size', 'Current task queue size', ['priority'])
TASK_PROCESSING_TIME = Histogram(
    'task_processing_seconds',
    'Time spent processing tasks',
    ['type']
)

class MetricsCollector:
    """Collects and manages system metrics"""
    
    def __init__(self):
        self.start_time = time.time()
        self._task_timings = {}

    def start_task_timer(self, task_id: str, task_type: str):
        """Start timing a task"""
        self._task_timings[task_id] = {
            'start_time': time.time(),
            'type': task_type
        }

    def stop_task_timer(self, task_id: str, status: str):
        """Stop timing a task and record metrics"""
        if task_id in self._task_timings:
            elapsed = time.time() - self._task_timings[task_id]['start_time']
            task_type = self._task_timings[task_id]['type']
            
            # Record metrics
            TASK_PROCESSING_TIME.labels(type=task_type).observe(elapsed)
            TASK_STATUS.labels(status=status).inc()
            
            # Cleanup
            del self._task_timings[task_id]

    def record_worker_metrics(self, worker_id: str, metrics: Dict):
        """Record worker metrics"""
        WORKER_TASKS.labels(
            worker_id=worker_id,
            status='completed'
        ).inc(metrics.get('completed_tasks', 0))
        
        WORKER_TASKS.labels(
            worker_id=worker_id,
            status='failed'
        ).inc(metrics.get('failed_tasks', 0))
        
        if 'processing_time' in metrics:
            WORKER_PROCESSING_TIME.labels(
                worker_id=worker_id
            ).observe(metrics['processing_time'])

    def record_agent_metrics(self, agent_id: str, agent_type: str, metrics: Dict):
        """Record agent metrics"""
        AGENT_TASKS.labels(
            agent_id=agent_id,
            type=agent_type
        ).inc(metrics.get('completed_tasks', 0))
        
        AGENT_ERRORS.labels(
            agent_id=agent_id,
            type=agent_type
        ).inc(metrics.get('errors', 0))
        
        if 'processing_time' in metrics:
            AGENT_PROCESSING_TIME.labels(
                agent_id=agent_id,
                type=agent_type
            ).observe(metrics['processing_time'])

    def update_queue_metrics(self, queue_sizes: Dict[str, int]):
        """Update task queue metrics"""
        for priority, size in queue_sizes.items():
            TASK_QUEUE_SIZE.labels(priority=priority).set(size)

    def update_system_metrics(self, metrics: Dict):
        """Update system-level metrics"""
        SYSTEM_MEMORY.set(metrics.get('memory_usage', 0))
        SYSTEM_CPU.set(metrics.get('cpu_usage', 0))
        SYSTEM_DISK.set(metrics.get('disk_usage', 0))

    def update_counts(self, worker_count: int, agent_count: int):
        """