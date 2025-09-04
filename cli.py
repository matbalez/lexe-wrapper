#!/usr/bin/env python3
"""
Lexe Wrapper CLI - Command-line interface for testing and demonstrating the Lexe wrapper.

This provides a simple CLI to interact with the LexeManager and test the functionality.
"""

import argparse
import os
import sys
import json
from pathlib import Path
from lexe_wrapper import LexeManager


def main():
    parser = argparse.ArgumentParser(
        description="Lexe Wrapper CLI - Simple utility for managing Lexe sidecar",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py start                    # Start sidecar with credentials from env
  python cli.py start --credentials "..." # Start with specific credentials
  python cli.py status                   # Check sidecar status
  python cli.py node-info               # Get node information
  python cli.py stop                    # Stop the sidecar
  python cli.py download                # Just download the binary

Environment Variables:
  LEXE_CLIENT_CREDENTIALS - Base64 encoded client credentials
        """
    )
    
    parser.add_argument(
        "command",
        choices=["start", "stop", "status", "node-info", "download", "health"],
        help="Command to execute"
    )
    
    parser.add_argument(
        "--credentials",
        help="Base64 encoded Lexe client credentials (overrides LEXE_CLIENT_CREDENTIALS env var)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=5393,
        help="Port for sidecar to listen on (default: 5393)"
    )
    
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Timeout for health checks in seconds (default: 30)"
    )
    
    parser.add_argument(
        "--no-wait",
        action="store_true",
        help="Don't wait for health check when starting"
    )
    
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Set up logging level
    if args.verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize LexeManager
    try:
        manager = LexeManager(
            client_credentials=args.credentials,
            port=args.port
        )
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    
    # Execute commands
    try:
        if args.command == "download":
            print("Downloading Lexe sidecar binary...")
            binary_path = manager.download_sidecar_binary()
            print(f"✓ Binary ready at: {binary_path}")
            
        elif args.command == "start":
            if not manager.client_credentials:
                print("Error: Client credentials are required. Set LEXE_CLIENT_CREDENTIALS or use --credentials", file=sys.stderr)
                return 1
            
            print("Starting Lexe sidecar...")
            if manager.start_sidecar(wait_for_health=not args.no_wait, health_timeout=args.timeout):
                print(f"✓ Sidecar started successfully on port {args.port}")
                if not args.no_wait:
                    print("✓ Health check passed")
            else:
                print("✗ Failed to start sidecar", file=sys.stderr)
                return 1
        
        elif args.command == "stop":
            print("Stopping Lexe sidecar...")
            if manager.stop_sidecar():
                print("✓ Sidecar stopped")
            else:
                print("✗ Failed to stop sidecar", file=sys.stderr)
                return 1
        
        elif args.command == "status":
            is_running = manager.is_running()
            is_healthy = manager.check_health() if is_running else False
            
            print(f"Sidecar process: {'Running' if is_running else 'Not running'}")
            if is_running:
                print(f"Health status: {'Healthy' if is_healthy else 'Unhealthy'}")
                print(f"URL: {manager.base_url}")
        
        elif args.command == "health":
            if manager.check_health():
                print("✓ Sidecar is healthy")
            else:
                print("✗ Sidecar is not healthy")
                return 1
        
        elif args.command == "node-info":
            try:
                node_info = manager.get_node_info()
                print("Node Information:")
                print(json.dumps(node_info, indent=2))
            except Exception as e:
                print(f"✗ Failed to get node info: {e}", file=sys.stderr)
                return 1
        
        return 0
        
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())