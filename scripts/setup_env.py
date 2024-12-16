import os
import sys
import subprocess
from pathlib import Path

def load_env_file(env_file):
    """Load environment variables from file"""
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                key, value = line.split('=', 1)
                os.environ[key] = value

def set_heroku_vars(env_file, app_name=None):
    """Set Heroku environment variables from file"""
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                key, value = line.split('=', 1)
                cmd = ['heroku', 'config:set', f'{key}={value}']
                if app_name:
                    cmd.extend(['-a', app_name])
                subprocess.run(cmd)

def main():
    """Main function to set up environment variables"""
    if len(sys.argv) < 2:
        print("Usage: python setup_env.py [local|heroku] [app_name]")
        sys.exit(1)

    env_type = sys.argv[1]
    app_name = sys.argv[2] if len(sys.argv) > 2 else None
    
    base_dir = Path(__file__).parent.parent
    
    if env_type == 'local':
        env_file = base_dir / '.env.development'
        load_env_file(env_file)
        print("Local environment variables set")
    
    elif env_type == 'heroku':
        env_file = base_dir / '.env.production'
        set_heroku_vars(env_file, app_name)
        print(f"Heroku environment variables set for app: {app_name}")
    
    else:
        print(f"Unknown environment type: {env_type}")
        sys.exit(1)

if __name__ == '__main__':
    main()