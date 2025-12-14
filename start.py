#!/usr/bin/env python3
"""
Railway startup script for IOS System
Handles PORT environment variable correctly
"""
import os
import sys
import subprocess

# Get PORT from environment, default to 8080
port = os.environ.get('PORT', '8080')

# Ensure we're in the correct directory
os.chdir('/app/ios-system')

# Build uvicorn command
cmd = [
    'uvicorn',
    'ios_bootstrap.main:app',
    '--host', '0.0.0.0',
    '--port', port
]

print(f"Starting uvicorn on port {port}")
print(f"Command: {' '.join(cmd)}")

# Execute uvicorn
sys.exit(subprocess.call(cmd))
