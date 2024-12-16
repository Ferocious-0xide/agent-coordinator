#!/usr/bin/env python
import os
import sys
import yaml
import subprocess
from typing import Dict

def load_formation_config() -> Dict:
    """Load the formation configuration from yaml"""
    config_path = os.path.join('deployment', 'heroku', 'formation.yml')
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def scale_dynos(app_name: str, environment: str = 'default'):
    """Scale dynos according to configuration"""
    config = load_formation_config()
    env_config = config.get(environment, config['default'])
    
    print(f"Scaling {app_name} to {environment} configuration...")
    
    for process_type, settings in env_config.items():
        quantity = settings['quantity']
        size = settings['size']
        
        # Scale process count
        subprocess.run([
            'heroku', 'ps:scale',
            f'{process_type}={quantity}',
            '-a', app_name
        ])
        
        # Set dyno size
        subprocess.run([
            'heroku', 'ps:type',
            f'{process_type}={size}',
            '-a', app_name
        ])
        
        print(f"Scaled {process_type} to {quantity} x {size}")

def setup_autoscaling(app_name: str):
    """Setup Heroku autoscaling"""
    # Web dynos autoscaling
    subprocess.run([
        'heroku', 'ps:autoscale:enable',
        'web',
        '--min', '1',
        '--max', '4',
        '--p95', '0.9',
        '-a', app_name
    ])
    
    # Worker dynos autoscaling
    subprocess.run([
        'heroku', 'ps:autoscale:enable',
        'worker',
        '--min', '2',
        '--max', '6',
        '--queue', 'jobs',
        '--target', '100',
        '-a', app_name
    ])

def main():
    if len(sys.argv) < 2:
        print("Usage: python scale_dynos.py APP_NAME [environment] [--autoscale]")
        sys.exit(1)
    
    app_name = sys.argv[1]
    environment = sys.argv[2] if len(sys.argv) > 2 else 'default'
    enable_autoscale = '--autoscale' in sys.argv
    
    # Scale dynos according to configuration
    scale_dynos(app_name, environment)
    
    # Setup autoscaling if requested
    if enable_autoscale:
        setup_autoscaling(app_name)

if __name__ == '__main__':
    main()