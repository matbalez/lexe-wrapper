"""
Lexe Wrapper - Simple Python package for integrating with Lexe Bitcoin Lightning Network wallet

This package provides a LexeManager class that handles the common gotchas when
integrating with the Lexe Sidecar SDK:
1. Downloading and extracting the binary
2. Starting the sidecar
3. Handling client credentials in base64 format
4. Managing the connection and health checks
"""

from .manager import LexeManager

__version__ = "1.0.0"
__author__ = "Lexe Wrapper Team"
__email__ = "support@example.com"

# Make LexeManager available at package level
__all__ = ['LexeManager']