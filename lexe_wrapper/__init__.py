"""
Lexe Wrapper - Unofficial Python package for integrating with Lexe Bitcoin Lightning Network wallet

DISCLAIMER: This is an unofficial, open-source wrapper around the Lexe Sidecar SDK.
It is not officially associated with or endorsed by Lexe.

This package provides a LexeManager class that handles the common gotchas when
integrating with the Lexe Sidecar SDK:
1. Downloading and extracting the binary
2. Starting the sidecar
3. Handling client credentials in base64 format
4. Managing the connection and health checks

License: MIT (see LICENSE file)
"""

from .manager import LexeManager

__version__ = "1.2.0"
__author__ = "Mat Balez"
__email__ = "matbalez@gmail.com"

# Make LexeManager available at package level
__all__ = ['LexeManager']