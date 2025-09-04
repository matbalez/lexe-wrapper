#!/usr/bin/env python3
"""
CLI entry point for lexe-wrapper package.
Allows running: python -m lexe_wrapper <command>
"""

import sys
import argparse
from .manager import LexeManager

def main():
    """Simple CLI for lexe-wrapper demonstration."""
    parser = argparse.ArgumentParser(
        description="Lexe Bitcoin Lightning Network Wrapper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m lexe_wrapper --help          Show this help
  pip install lexe-wrapper               Install from PyPI
  
For development usage:
  from lexe_wrapper import LexeManager
  with LexeManager() as lexe:
      lexe.start_sidecar()
        """
    )
    
    parser.add_argument(
        "--version", 
        action="version", 
        version="lexe-wrapper 1.0.0"
    )
    
    parser.add_argument(
        "--info",
        action="store_true",
        help="Show package information"
    )
    
    args = parser.parse_args()
    
    if args.info:
        print("🚀 lexe-wrapper v1.0.0")
        print("📦 Python wrapper for Lexe Bitcoin Lightning Network wallet")
        print("🌐 PyPI: https://pypi.org/project/lexe-wrapper/")
        print("💻 Install: pip install lexe-wrapper")
        print("")
        print("✨ Eliminates setup friction for Bitcoin Lightning development")
        print("⚡ Get Lightning payments working in under 30 seconds!")
        return 0
    
    # Default: show help
    parser.print_help()
    return 0

if __name__ == "__main__":
    sys.exit(main())