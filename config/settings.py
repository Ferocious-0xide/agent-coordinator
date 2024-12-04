from typing import Dict, Any
import os
from pathlib import Path

# Base path configuration
BASE_DIR = Path(__file__).resolve().parent.parent

# Environment-based configuration
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')

# Redis Configuration
REDIS_CONFIG = {
    'host': os.getenv('REDIS_HOST', 'localhost'),
    'port': int(os.getenv('REDIS_PORT', 6379)),
    'db': int(os.getenv('REDIS_DB', 0)),
    'password': os.getenv('REDIS_PASSWORD', None),
    'ssl': os.getenv('REDIS_SSL', 'False').lower() == 'true'
}

# Worker Configuration
WORKER_CONFIG = {
    'max_concurrent_tasks': int(os.getenv('MAX_CONCURRENT_TASKS', 3)),
    'task_timeout': int(os.getenv('TASK_TIMEOUT', 300)),  # seconds
    'retry_attempts': int(os.getenv('RETRY_ATTEMPTS', 3)),
    'retry_delay': int(os.getenv('RETRY_DELAY', 5)),  # seconds
}

# Agent Configuration
AGENT_CONFIG = {
    'default_llm': os.getenv('DEFAULT_LLM', 'gpt-4'),
    'max_tokens': int(os.getenv('MAX_TOKENS', 2000)),
    'temperature': float(os.getenv('TEMPERATURE', 0.7)),
    'max_retries': int(os.getenv('AGENT_MAX_RETRIES', 3))
}

# Queue Configuration
QUEUE_CONFIG = {
    'default_timeout': int(os.getenv('QUEUE_TIMEOUT', 600)),  # seconds
    'max_queue_size': int(os.getenv('MAX_QUEUE_SIZE', 1000)),
    'priority_levels': int(os.getenv('PRIORITY_LEVELS', 3))
}

# Task Configuration
TASK_CONFIG = {
    'max_lifetime': int(os.getenv('TASK_MAX_LIFETIME', 3600)),  # seconds
    'cleanup_interval': int(os.getenv('CLEANUP_INTERVAL', 300))  # seconds
}

# Monitoring Configuration
MONITORING_CONFIG = {
    'health_check_interval': int(os.getenv('HEALTH_CHECK_INTERVAL', 60)),  # seconds
    'metrics_collection_interval': int(os.getenv('METRICS_INTERVAL', 30)),  # seconds
    'alert_threshold': int(os.getenv('ALERT_THRESHOLD', 90))  # percentage
}

# CPU Configuration for ML frameworks
CPU_CONFIG = {
    'torch_num_threads': int(os.getenv('TORCH_NUM_THREADS', 4)),
    'tf_num_threads': int(os.getenv('TF_NUM_THREADS', 4)),
    'mkl_num_threads': int(os.getenv('MKL_NUM_THREADS', 4))
}

# API Configuration
API_CONFIG = {
    'rate_limit': int(os.getenv('RATE_LIMIT', 100)),  # requests per minute
    'timeout': int(os.getenv('API_TIMEOUT', 30)),  # seconds
}

def get_config() -> Dict[str, Any]:
    """Returns the complete configuration dictionary based on environment"""
    return {
        'environment': ENVIRONMENT,
        'redis': REDIS_CONFIG,
        'worker': WORKER_CONFIG,
        'agent': AGENT_CONFIG,
        'queue': QUEUE_CONFIG,
        'task': TASK_CONFIG,
        'monitoring': MONITORING_CONFIG,
        'cpu': CPU_CONFIG,
        'api': API_CONFIG
    }