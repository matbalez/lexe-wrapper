#!/usr/bin/env python3
"""
CLI entry point for lexe-wrapper package.
Allows running: python -m lexe_wrapper <command>
"""

import sys
import os

# Add the parent directory to the path so we can import cli
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cli import main

if __name__ == "__main__":
    sys.exit(main())