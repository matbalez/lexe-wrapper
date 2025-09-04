"""
Lexe Wrapper - Simple utility for integrating with Lexe Bitcoin Lightning Network wallet

This module provides a LexeManager class that handles the common gotchas when
integrating with the Lexe Sidecar SDK:
1. Downloading and extracting the binary
2. Starting the sidecar
3. Handling client credentials in base64 format
4. Managing the connection and health checks
"""

import os
import subprocess
import requests
import logging
import time
import zipfile
import urllib.request
import base64
from pathlib import Path
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class LexeManager:
    """
    Manages the Lexe sidecar process and provides a simple interface for developers
    to get Lexe working quickly and easily.
    """
    
    def __init__(self, client_credentials: Optional[str] = None, port: int = 5393):
        """
        Initialize the LexeManager.
        
        Args:
            client_credentials: Base64 encoded Lexe client credentials. 
                              If None, will try to read from LEXE_CLIENT_CREDENTIALS env var.
            port: Port for the sidecar to listen on (default: 5393)
        """
        self.port = port
        self.base_url = f"http://localhost:{port}"
        self.sidecar_process: Optional[subprocess.Popen] = None
        self.bin_dir = Path("./bin")
        self.sidecar_path = self.bin_dir / "lexe-sidecar"
        
        # Handle client credentials
        self.client_credentials = client_credentials or os.getenv("LEXE_CLIENT_CREDENTIALS")
        if self.client_credentials:
            self.client_credentials = self._validate_and_fix_credentials(self.client_credentials)
        else:
            logger.warning("No LEXE_CLIENT_CREDENTIALS provided. You'll need to set this before starting the sidecar.")
    
    def _validate_and_fix_credentials(self, credentials: str) -> str:
        """
        Validate and fix base64 padding for client credentials.
        
        Args:
            credentials: Base64 encoded credentials string
            
        Returns:
            Properly formatted base64 credentials
            
        Raises:
            ValueError: If credentials are invalid
        """
        # Clean up the credentials (remove quotes and whitespace)
        credentials = credentials.strip().strip('"').strip("'").strip()
        
        try:
            # Add padding if missing
            missing_padding = len(credentials) % 4
            if missing_padding:
                credentials += '=' * (4 - missing_padding)
            
            # Validate it's proper base64
            base64.b64decode(credentials)
            logger.info("Client credentials validated successfully")
            return credentials
            
        except Exception as e:
            raise ValueError(f"Invalid client credentials format: {e}")
    
    def download_sidecar_binary(self) -> str:
        """
        Download and extract the latest Lexe sidecar binary for x86 Linux.
        
        Returns:
            Path to the extracted binary
        """
        # Create bin directory
        self.bin_dir.mkdir(exist_ok=True)
        
        # Check if binary already exists
        if self.sidecar_path.exists():
            logger.info("Lexe sidecar binary already exists")
            return str(self.sidecar_path)
        
        # Download the latest release (v0.2.0 is the latest as of the documentation)
        zip_url = "https://github.com/lexe-app/lexe-sidecar-sdk/releases/download/lexe-sidecar-v0.2.0/lexe-sidecar-linux-x86_64.zip"
        zip_path = self.bin_dir / "lexe-sidecar.zip"
        
        logger.info(f"Downloading Lexe sidecar from {zip_url}")
        try:
            urllib.request.urlretrieve(zip_url, zip_path)
            logger.info(f"Downloaded to {zip_path}")
        except Exception as e:
            logger.error(f"Failed to download Lexe sidecar: {e}")
            raise
        
        # Extract the binary
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.bin_dir)
            logger.info(f"Extracted to {self.bin_dir}")
        except Exception as e:
            logger.error(f"Failed to extract Lexe sidecar: {e}")
            raise
        
        # Make it executable
        try:
            self.sidecar_path.chmod(0o755)
            logger.info(f"Made {self.sidecar_path} executable")
        except Exception as e:
            logger.error(f"Failed to make sidecar executable: {e}")
            raise
        
        # Clean up zip file
        try:
            zip_path.unlink()
            logger.info("Cleaned up zip file")
        except Exception as e:
            logger.warning(f"Failed to clean up zip file: {e}")
        
        logger.info(f"Lexe sidecar ready at {self.sidecar_path}")
        return str(self.sidecar_path)
    
    def start_sidecar(self, wait_for_health: bool = True, health_timeout: int = 30) -> bool:
        """
        Start the Lexe sidecar process.
        
        Args:
            wait_for_health: Whether to wait for the health check to pass
            health_timeout: Timeout in seconds for health check
            
        Returns:
            True if started successfully, False otherwise
        """
        if not self.client_credentials:
            raise ValueError("Client credentials are required to start the sidecar. Set LEXE_CLIENT_CREDENTIALS or pass credentials to constructor.")
        
        # Check if already running
        if self.sidecar_process and self.sidecar_process.poll() is None:
            logger.info("Lexe sidecar is already running")
            return True
        
        # Download binary if needed
        self.download_sidecar_binary()
        
        # Start the sidecar process
        logger.info("Starting Lexe sidecar process")
        try:
            cmd = [
                str(self.sidecar_path),
                "--listen-addr", f"0.0.0.0:{self.port}",
                "--client-credentials", self.client_credentials
            ]
            
            self.sidecar_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            logger.info(f"Sidecar process started with PID {self.sidecar_process.pid}")
            
            # Wait for health check if requested
            if wait_for_health:
                if self.wait_for_health(timeout=health_timeout):
                    logger.info("Sidecar is healthy and ready")
                    return True
                else:
                    logger.error("Sidecar failed health check")
                    self.stop_sidecar()
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start sidecar: {e}")
            return False
    
    def stop_sidecar(self) -> bool:
        """
        Stop the Lexe sidecar process.
        
        Returns:
            True if stopped successfully, False otherwise
        """
        if not self.sidecar_process:
            logger.info("No sidecar process to stop")
            return True
        
        try:
            self.sidecar_process.terminate()
            
            # Wait for graceful shutdown
            try:
                self.sidecar_process.wait(timeout=5)
                logger.info("Sidecar stopped gracefully")
            except subprocess.TimeoutExpired:
                # Force kill if it doesn't stop gracefully
                self.sidecar_process.kill()
                self.sidecar_process.wait()
                logger.info("Sidecar forcefully stopped")
            
            self.sidecar_process = None
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop sidecar: {e}")
            return False
    
    def check_health(self) -> bool:
        """
        Check if the sidecar is healthy and responding.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            response = requests.get(f"{self.base_url}/v1/health", timeout=5)
            return response.status_code == 200 and response.json().get("status") == "ok"
        except Exception:
            return False
    
    def wait_for_health(self, timeout: int = 30, check_interval: float = 1.0) -> bool:
        """
        Wait for the sidecar to become healthy.
        
        Args:
            timeout: Maximum time to wait in seconds
            check_interval: Time between health checks in seconds
            
        Returns:
            True if becomes healthy within timeout, False otherwise
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.check_health():
                return True
            time.sleep(check_interval)
        
        return False
    
    def get_node_info(self) -> Dict[str, Any]:
        """
        Get node information from the Lexe API.
        
        Returns:
            Node information dictionary
            
        Raises:
            requests.RequestException: If the API call fails
        """
        try:
            response = requests.get(f"{self.base_url}/v1/node/node_info", timeout=15)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get node info: {e}")
            raise
    
    def is_running(self) -> bool:
        """
        Check if the sidecar process is currently running.
        
        Returns:
            True if running, False otherwise
        """
        return self.sidecar_process is not None and self.sidecar_process.poll() is None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures sidecar is stopped."""
        self.stop_sidecar()
    
    def start_for_webapp(self, health_timeout: int = 30) -> bool:
        """
        Start the sidecar for a web application with appropriate error handling.
        This method is specifically designed for web app initialization.
        
        Args:
            health_timeout: Timeout in seconds for health check
            
        Returns:
            True if started successfully and ready for web app use
            
        Raises:
            RuntimeError: If startup fails with detailed error message
        """
        try:
            if not self.start_sidecar(wait_for_health=True, health_timeout=health_timeout):
                raise RuntimeError("Failed to start Lexe sidecar - check credentials and network connectivity")
            
            logger.info(f"Lexe sidecar ready for web app at {self.base_url}")
            return True
            
        except Exception as e:
            error_msg = f"Web app Lexe initialization failed: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
    
    def ensure_running(self) -> bool:
        """
        Ensure the sidecar is running and healthy. Useful for web app health checks.
        
        Returns:
            True if running and healthy, False otherwise
        """
        return self.is_running() and self.check_health()
    
    def restart_if_needed(self) -> bool:
        """
        Restart the sidecar if it's not running or unhealthy.
        Useful for web app recovery scenarios.
        
        Returns:
            True if now running and healthy, False if restart failed
        """
        if self.ensure_running():
            return True
        
        logger.warning("Sidecar not healthy, attempting restart...")
        
        # Stop if partially running
        if self.is_running():
            self.stop_sidecar()
        
        # Restart
        try:
            return self.start_sidecar(wait_for_health=True)
        except Exception as e:
            logger.error(f"Failed to restart sidecar: {e}")
            return False