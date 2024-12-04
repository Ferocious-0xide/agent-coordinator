import os
import logging.config
from pathlib import Path

# Logging paths
LOG_DIR = Path(__file__).resolve().parent.parent / 'logs'
LOG_DIR.mkdir(exist_ok=True)

# Logging configuration dictionary
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
        'detailed': {
            'format': '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'standard',
            'stream': 'ext://sys.stdout'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'DEBUG',
            'formatter': 'detailed',
            'filename': LOG_DIR / 'coordinator.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'encoding': 'utf8'
        },
        'error_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'ERROR',
            'formatter': 'detailed',
            'filename': LOG_DIR / 'error.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'encoding': 'utf8'
        },
    },
    'loggers': {
        '': {  # root logger
            'handlers': ['console', 'file', 'error_file'],
            'level': os.getenv('ROOT_LOG_LEVEL', 'INFO'),
            'propagate': True
        },
        'coordinator': {
            'handlers': ['console', 'file', 'error_file'],
            'level': os.getenv('COORDINATOR_LOG_LEVEL', 'DEBUG'),
            'propagate': False
        },
        'worker': {
            'handlers': ['console', 'file', 'error_file'],
            'level': os.getenv('WORKER_LOG_LEVEL', 'DEBUG'),
            'propagate': False
        },
        'agent': {
            'handlers': ['console', 'file', 'error_file'],
            'level': os.getenv('AGENT_LOG_LEVEL', 'DEBUG'),
            'propagate': False
        }
    }
}

def setup_logging():
    """Initialize logging configuration"""
    logging.config.dictConfig(LOGGING_CONFIG)
    
    # Create logger instance
    logger = logging.getLogger(__name__)
    logger.info('Logging system initialized')
    
    return logger