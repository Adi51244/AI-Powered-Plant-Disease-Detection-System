#!/usr/bin/env python3
import os
import subprocess
import sys

def main():
    # Get port from environment, default to 8080
    port = os.environ.get('PORT', '8080')
    
    print(f"Starting LeafIQ on port {port}...")
    
    # Build gunicorn command
    cmd = [
        'gunicorn',
        f'--bind=0.0.0.0:{port}',
        'app:app',
        '--timeout=900',
        '--workers=1',
        '--access-logfile=-',
        '--error-logfile=-'
    ]
    
    # Execute gunicorn
    try:
        subprocess.exec_module_shim = None  # Avoid any import issues
        os.execvp('gunicorn', cmd)
    except Exception as e:
        print(f"Error starting gunicorn: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
