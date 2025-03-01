#!/usr/bin/env python3
"""
Code Map Generator Wrapper

This script provides an easy way to generate a code map from the root directory.
It calls the implementation in utils/generate_code_map.py.

Usage:
    python generate_code_map.py [--detailed] [--output OUTPUT_PATH]
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    # Get the directory where this script is located (should be the repo root)
    repo_root = os.path.dirname(os.path.abspath(__file__))
    
    # Path to the actual implementation
    impl_path = os.path.join(repo_root, "utils", "generate_code_map.py")
    
    # Make sure the implementation exists
    if not os.path.exists(impl_path):
        print(f"Error: Could not find {impl_path}")
        sys.exit(1)
    
    # Forward all arguments to the implementation
    cmd = [sys.executable, impl_path] + sys.argv[1:]
    
    # Run the implementation with the same arguments
    subprocess.run(cmd)

if __name__ == "__main__":
    main() 