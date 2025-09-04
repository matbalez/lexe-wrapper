# Lexe Wrapper

## Overview
A simple Python utility for integrating with the Lexe Bitcoin Lightning Network wallet. This wrapper simplifies the setup and management of the Lexe Sidecar SDK by handling the common gotchas like binary download, process management, credentials handling, and health checking.

## Recent Changes
- Completed Lexe wrapper implementation (September 4, 2025)
- All core functionality implemented: binary download, process management, credentials handling, health checking
- CLI interface created for testing and demonstration
- Comprehensive documentation written for developers and coding agents
- Successfully tested with real Lexe node: connected, retrieved node info, created invoices, confirmed API access

## User Preferences
- Focus on simplicity and clean interfaces
- Use the Lexe Sidecar API directly without additional abstraction layers
- Provide clear documentation for developers and coding agents

## Project Architecture
- `lexe_manager.py`: Main LexeManager class for sidecar management
- `cli.py`: Command-line interface for testing and demonstration
- Uses Python standard library and minimal dependencies (only requests)
- Downloads latest Lexe sidecar binary automatically
- Handles base64 credential encoding and validation
- Manages sidecar subprocess lifecycle