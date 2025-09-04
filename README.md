# Lexe Wrapper

A simple Python utility for integrating with the Lexe Bitcoin Lightning Network wallet. This wrapper eliminates common setup gotchas when using the Lexe Sidecar SDK, making it easy for developers and coding agents to "get Lexe going" quickly.

## What This Wrapper Solves

The Lexe Sidecar API is already clean and simple, but there are several setup gotchas that slow down development:

1. **Binary Management**: Downloading and extracting the correct Lexe sidecar binary
2. **Process Management**: Starting and stopping the sidecar subprocess
3. **Credentials Handling**: Properly encoding and validating base64 client credentials
4. **Connection Management**: Ensuring the sidecar is healthy and ready to accept requests
5. **Port Configuration**: Managing the correct port (5393) for communication

This wrapper handles all of these automatically, so you can focus on using the Lexe API.

## Quick Start

### 1. Get Your Lexe Client Credentials

You need a Lexe wallet and client credentials. Follow the [Lexe SDK documentation](https://github.com/lexe-app/lexe-sidecar-sdk) to:
1. Download the Lexe mobile app
2. Create a wallet 
3. Export client credentials (base64 encoded string)

### 2. Set Up Environment

```bash
# Set your credentials (required)
export LEXE_CLIENT_CREDENTIALS="your_base64_encoded_credentials_here"

# Install Python dependencies
pip install requests
```

### 3. Use the Wrapper

#### Option A: Command Line Interface

```bash
# Download the sidecar binary
python cli.py download

# Start the sidecar (downloads binary automatically if needed)
python cli.py start

# Check status
python cli.py status

# Get node information
python cli.py node-info

# Stop the sidecar
python cli.py stop
```

#### Option B: Python Code

```python
from lexe_manager import LexeManager
import requests

# Initialize and start Lexe
with LexeManager() as lexe:
    # Start the sidecar (handles download, startup, health check)
    lexe.start_sidecar()
    
    # Now use the standard Lexe Sidecar API directly
    # Create an invoice
    response = requests.post("http://localhost:5393/v1/node/create_invoice", json={
        "amount": "1000", 
        "description": "Test payment"
    })
    invoice_data = response.json()
    
    # Check payment status
    response = requests.get("http://localhost:5393/v1/node/payment", 
                          params={"index": invoice_data["index"]})
    payment_status = response.json()
    
    # The sidecar automatically stops when exiting the context
```

#### Option C: Manual Management

```python
from lexe_manager import LexeManager

# Initialize
lexe = LexeManager()

# Start manually
lexe.start_sidecar()

# Check if healthy
if lexe.check_health():
    print("Lexe is ready!")
    
    # Get node info using the wrapper method
    node_info = lexe.get_node_info()
    print(f"Balance: {node_info['balance']} sats")

# Stop when done
lexe.stop_sidecar()
```

## For Coding Agents

When using this wrapper in automated coding environments:

### Essential Setup Steps
1. **Set credentials**: `export LEXE_CLIENT_CREDENTIALS="your_credentials"`
2. **Install dependency**: `pip install requests`
3. **Import and start**: Use the context manager pattern for automatic cleanup

### Example Implementation
```python
from lexe_manager import LexeManager
import requests

def setup_lexe_integration():
    """Initialize Lexe for your application"""
    lexe = LexeManager()
    lexe.start_sidecar()  # Downloads binary, starts process, waits for health
    return "http://localhost:5393"  # Ready to use Lexe API

def create_lightning_invoice(amount_sats, description):
    """Create a Lightning invoice using Lexe API"""
    response = requests.post("http://localhost:5393/v1/node/create_invoice", json={
        "amount": str(amount_sats),
        "description": description
    })
    return response.json()

# The wrapper handles all the complexity - just use the API directly!
```

### Key Benefits for Automation
- **Zero configuration files needed** - everything is handled programmatically
- **Automatic binary management** - downloads and extracts the right version
- **Built-in health checks** - ensures the connection is ready before returning
- **Error handling** - clear error messages when credentials are invalid or missing
- **Process lifecycle management** - clean startup and shutdown

## API Reference

### LexeManager Class

#### Constructor
```python
LexeManager(client_credentials=None, port=5393)
```
- `client_credentials`: Base64 encoded credentials (uses `LEXE_CLIENT_CREDENTIALS` env var if None)
- `port`: Port for sidecar to listen on (default: 5393)

#### Methods

**`start_sidecar(wait_for_health=True, health_timeout=30)`**
- Downloads binary if needed, starts process, optionally waits for health check
- Returns: `bool` - True if started successfully

**`stop_sidecar()`**
- Gracefully stops the sidecar process
- Returns: `bool` - True if stopped successfully

**`check_health()`**
- Checks if sidecar is responding to health checks
- Returns: `bool` - True if healthy

**`get_node_info()`**
- Gets node information from Lexe API
- Returns: `dict` - Node information including balance, channels, etc.

**`download_sidecar_binary()`**
- Downloads and extracts the latest Lexe sidecar binary
- Returns: `str` - Path to extracted binary

**`is_running()`**
- Checks if the sidecar process is currently running
- Returns: `bool` - True if running

## CLI Reference

```bash
python cli.py <command> [options]

Commands:
  start       Start the sidecar
  stop        Stop the sidecar  
  status      Show sidecar status
  health      Check sidecar health
  node-info   Get node information
  download    Download sidecar binary only

Options:
  --credentials TEXT    Override credentials from env var
  --port INTEGER       Port for sidecar (default: 5393)
  --timeout INTEGER    Health check timeout (default: 30)
  --no-wait           Don't wait for health check when starting
  --verbose           Enable verbose logging
```

## After Starting the Sidecar

Once the wrapper starts the sidecar, you can use the [standard Lexe Sidecar API](https://github.com/lexe-app/lexe-sidecar-sdk#rest-api-reference) directly:

- **Health**: `GET http://localhost:5393/v1/health`
- **Node Info**: `GET http://localhost:5393/v1/node/node_info`
- **Create Invoice**: `POST http://localhost:5393/v1/node/create_invoice`
- **Pay Invoice**: `POST http://localhost:5393/v1/node/pay_invoice`
- **Check Payment**: `GET http://localhost:5393/v1/node/payment?index=<index>`

## Error Handling

The wrapper provides clear error messages for common issues:

- **Missing credentials**: Clear message about setting `LEXE_CLIENT_CREDENTIALS`
- **Invalid credentials**: Validates base64 format and provides specific error
- **Download failures**: Network issues when downloading the binary
- **Health check failures**: When sidecar doesn't respond within timeout
- **Process management**: Issues starting or stopping the sidecar process

## Requirements

- Python 3.7+
- `requests` library
- x86_64 Linux environment (where Lexe sidecar runs)
- Valid Lexe client credentials

## License

MIT License - see LICENSE file for details.

## About

This wrapper is designed to eliminate the friction in getting started with Lexe Bitcoin Lightning Network integration. The Lexe Sidecar API itself is excellent - this just handles the setup complexity so you can focus on building great Lightning applications.