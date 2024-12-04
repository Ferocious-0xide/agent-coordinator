"""
CPU-specific tensor operation configurations
"""

import os
import logging

logger = logging.getLogger(__name__)

def configure_cpu_tensor_ops():
    """Configure tensor operations for CPU-only execution"""
    try:
        # TensorFlow CPU configuration
        import tensorflow as tf
        tf.config.set_visible_devices([], 'GPU')
        
        # Set number of threads
        tf.config.threading.set_inter_op_parallelism_threads(4)
        tf.config.threading.set_intra_op_parallelism_threads(4)
        
        logger.info("TensorFlow configured for CPU operations")
    except ImportError:
        logger.warning("TensorFlow not installed")

    try:
        # PyTorch CPU configuration
        import torch
        torch.set_num_threads(4)
        
        # Disable CUDA
        os.environ["CUDA_VISIBLE_DEVICES"] = ""
        
        logger.info("PyTorch configured for CPU operations")
    except ImportError:
        logger.warning("PyTorch not installed")

    # Configure MKL for CPU operations
    os.environ["MKL_NUM_THREADS"] = "4"
    os.environ["NUMEXPR_NUM_THREADS"] = "4"
    os.environ["OMP_NUM_THREADS"] = "4"