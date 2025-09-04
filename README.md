# Lexe Wrapper

A simple Python package for integrating Bitcoin Lightning Network payments using the Lexe wallet. Install with pip and start building Lightning apps in under 30 seconds.

```bash
pip install lexe-wrapper
```

> **⚠️ Important:** This is an unofficial, open-source wrapper around the Lexe Sidecar SDK. It is not officially associated with or endorsed by Lexe. This project is independently developed to help developers integrate with Lexe's Lightning wallet services.

## What This Package Solves

The Lexe Sidecar API is already clean and simple, but there are several setup gotchas that slow down development:

1. **Binary Management**: Downloading and extracting the correct Lexe sidecar binary
2. **Process Management**: Starting and stopping the sidecar subprocess  
3. **Credentials Handling**: Properly encoding and validating base64 client credentials
4. **Connection Management**: Ensuring the sidecar is healthy and ready to accept requests
5. **Port Configuration**: Managing the correct port (5393) for communication

This package handles all of these automatically, so you can focus on building great Lightning applications.

## ⚡ Quick Start (30 seconds)

### 1. Install from PyPI

```bash
pip install lexe-wrapper
```

### 2. Set Your Lexe Credentials

```bash
export LEXE_CLIENT_CREDENTIALS="your_base64_encoded_credentials_here"
```

*Need credentials? Get them from the [Lexe mobile app](https://github.com/lexe-app/lexe-sidecar-sdk) - create a wallet and export client credentials.*

### 3. Start Building Lightning Apps

#### Copy-Paste Example

```python
from lexe_wrapper import LexeManager
import requests

# Automatic setup and cleanup
with LexeManager() as lexe:
    lexe.start_sidecar()  # Downloads binary, starts process, health checks
    
    # Get node info and balance
    node_response = requests.get("http://localhost:5393/v1/node/node_info")
    node_info = node_response.json()
    print(f"💰 Wallet balance: {node_info['balance']} sats")
    
    # Create a Lightning invoice (uses standard Lexe API at localhost:5393)
    response = requests.post("http://localhost:5393/v1/node/create_invoice", json={
        "amount": "1000", 
        "description": "Test payment",
        "expiration_secs": 3600  # 1 hour expiration
    })
    invoice_data = response.json()
    
    # CRITICAL: Store payment_index for monitoring payment completion
    payment_index = invoice_data['index']  # Save this!
    
    print(f"⚡ Lightning invoice created successfully!")
    print(f"📋 Invoice: {invoice_data.get('invoice', 'Generated')[:50]}...")
    print(f"🔍 Payment index (save this): {payment_index}")
    
    # Sidecar automatically stops when exiting the context
```

**That's it!** Lightning payments are now working in your Python app. 🎉

## 🚨 Payment Tracking (CRITICAL - READ THIS FIRST!)

**Most developers miss this crucial step:** After creating an invoice, you MUST properly monitor for payment completion. This is the #1 integration issue.

### ⚠️ Index vs Hash - Critical Distinction

<div style="background-color: #fff3cd; border: 2px solid #ffc107; padding: 15px; border-radius: 5px;">
<strong>🚨 IMPORTANT: Use the `index` field, NOT payment_hash!</strong><br><br>
Unlike most Lightning APIs that use payment hashes, Lexe uses an <strong>index</strong> field for payment tracking:
<ul>
<li>✅ CORRECT: Use <code>invoice_data['index']</code> from invoice creation</li>
<li>❌ WRONG: Do NOT use payment_hash or invoice string for status checks</li>
</ul>
</div>

### Complete Payment Lifecycle Example

```python
from lexe_wrapper import LexeManager
import requests
import time

with LexeManager() as lexe:
    lexe.start_sidecar()
    
    # Step 1: Create invoice and GET THE INDEX
    response = requests.post("http://localhost:5393/v1/node/create_invoice", json={
        "amount": "10000",  # 10,000 sats
        "description": "Payment for order #123",
        "expiration_secs": 600  # 10 minutes
    })
    invoice_data = response.json()
    
    # Step 2: CRITICAL - Store the payment index (NOT the invoice string!)
    payment_index = invoice_data['index']  # ← THIS IS WHAT YOU NEED!
    invoice_string = invoice_data['invoice']  # This is for the payer
    
    print(f"⚡ Invoice created: {invoice_string[:50]}...")
    print(f"📍 Payment Index: {payment_index}")  # Save this to your database!
    
    # Step 3: Monitor for payment completion
    print("⏳ Waiting for payment...")
    timeout = time.time() + 600  # 10 minute timeout
    
    while time.time() < timeout:
        # Check payment status using the INDEX
        status_response = requests.get(
            f"http://localhost:5393/v1/node/payment?index={payment_index}"
        )
        payment = status_response.json()
        
        # Step 4: Check for completion
        if payment['status'] == 'completed':  # ← "completed" NOT "settled"!
            print(f"✅ Payment received: {payment['amount']} sats")
            # Update your database, trigger order fulfillment, etc.
            break
        elif payment['status'] == 'failed':
            print("❌ Payment failed")
            break
        elif payment['status'] == 'cancelled':
            print("🚫 Payment cancelled")
            break
            
        time.sleep(2)  # Poll every 2 seconds
    else:
        print("⏰ Payment timeout - invoice expired")
```

### Payment Status Values

| Status | Meaning | Action Required |
|--------|---------|-----------------|
| `pending` | Invoice created, awaiting payment | Continue polling |
| `completed` | ✅ Payment received successfully | Stop polling, fulfill order |
| `failed` | Payment attempt failed | Stop polling, handle failure |
| `cancelled` | Invoice was cancelled | Stop polling |
| `expired` | Invoice expired without payment | Stop polling |

**Important:** The successful payment status is `completed`, NOT `settled` (common Lightning convention).

### Database Storage Pattern

```sql
-- Store payment tracking data properly
CREATE TABLE lightning_payments (
    id SERIAL PRIMARY KEY,
    payment_index VARCHAR(255) UNIQUE NOT NULL,  -- Critical: store the index!
    invoice_string TEXT NOT NULL,                -- For displaying to payer
    amount_sats BIGINT NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    paid_at TIMESTAMP,
    metadata JSONB
);

-- Example: After creating invoice
INSERT INTO lightning_payments (payment_index, invoice_string, amount_sats, description)
VALUES ($1, $2, $3, $4)
RETURNING id;

-- Example: Check status
UPDATE lightning_payments 
SET status = 'completed', paid_at = NOW()
WHERE payment_index = $1;
```

## Quick API Reference

### Key Endpoints You'll Use

| Endpoint | Method | Purpose | Critical Notes |
|----------|--------|---------|----------------|
| `/v1/node/create_invoice` | POST | Create Lightning invoice | **Returns `index` field - SAVE THIS!** |
| `/v1/node/payment?index={index}` | GET | Check payment status | **Use `index` from invoice creation** |
| `/v1/node/node_info` | GET | Get node info & balance | Returns balance in sats |
| `/v1/node/pay_invoice` | POST | Pay a Lightning invoice | Send payments |
| `/v1/node/decode_invoice` | POST | Decode invoice details | Validate before paying |

### Quick Integration Patterns

#### Basic Web App Setup

```python
from lexe_wrapper import LexeManager

# Initialize once when your web app starts
lexe = LexeManager()
lexe.start_for_webapp()  # Robust startup with error handling

# Use throughout your app's lifetime
@app.route('/create-invoice', methods=['POST'])
def create_invoice():
    response = requests.post("http://localhost:5393/v1/node/create_invoice", 
                           json=request.json)
    invoice_data = response.json()
    # ALWAYS save the index for payment tracking!
    save_to_database(invoice_data['index'], invoice_data['invoice'])
    return invoice_data

# Stop when app shuts down
lexe.stop_sidecar()
```

#### Manual Management

```python
from lexe_wrapper import LexeManager

lexe = LexeManager()

try:
    lexe.start_sidecar()
    
    if lexe.check_health():
        print("Lexe is ready!")
        
        # Get node info using the wrapper method
        node_info = lexe.get_node_info()
        print(f"Balance: {node_info['balance']} sats")
        
finally:
    lexe.stop_sidecar()
```

## For Coding Agents

When using this package in automated coding environments:

### Essential Setup Steps
1. **Install package**: `pip install lexe-wrapper`
2. **Set credentials**: `export LEXE_CLIENT_CREDENTIALS="your_credentials"`
3. **Import and start**: Use the context manager pattern for automatic cleanup

### Example Implementation
```python
from lexe_wrapper import LexeManager
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

# The package handles all the complexity - just use the API directly!
```

### Key Benefits for Automation
- **Standard pip installation** - `pip install lexe-wrapper` (published on PyPI)
- **Clean imports** - `from lexe_wrapper import LexeManager`
- **Zero configuration files needed** - everything is handled programmatically
- **Automatic binary management** - downloads and extracts the right version
- **Built-in health checks** - ensures the connection is ready before returning
- **Error handling** - clear error messages when credentials are invalid or missing
- **Process lifecycle management** - clean startup and shutdown

## Advanced Usage

### For Development from Source

If you want to contribute or modify the package:

```bash
git clone https://github.com/lexe-app/lexe-wrapper.git
cd lexe-wrapper
pip install -e .
```

## ⚡ Payment Monitoring (Critical Information)

Based on real developer feedback, here are the **essential patterns** for monitoring Lightning payments:

### 🚨 Critical Fixes (Must Read!)

**1. Payment Status Value**
```python
# ❌ WRONG - Documentation was incorrect
if payment['status'] == 'settled':

# ✅ CORRECT - API returns 'completed'
if payment['status'] == 'completed':
```

**2. Store Payment Index**
```python
# When creating invoice, MUST store the 'index' field!
response = requests.post("http://localhost:5393/v1/node/create_invoice", json={...})
invoice_data = response.json()

# CRITICAL: Store this for payment monitoring
payment_index = invoice_data['index']  # Required for status checking
payment_hash = invoice_data['payment_hash']  # Also recommended
```

**3. Correct API Endpoint**
```python
# Correct endpoint for payment status
endpoint = f"http://localhost:5393/v1/node/payment?index={payment_index}"
response = requests.get(endpoint)
```

### Complete Working Example

```python
from lexe_wrapper import LexeManager
import requests
import time

def complete_payment_flow():
    with LexeManager() as lexe:
        lexe.start_sidecar()
        
        # 1. Create invoice and store essential fields
        invoice_response = requests.post("http://localhost:5393/v1/node/create_invoice", json={
            "amount": "1000",
            "description": "Premium subscription",
            "expiration_secs": 3600
        })
        
        invoice_data = invoice_response.json()
        
        # CRITICAL: Store these fields in your database
        payment_record = {
            'invoice': invoice_data['invoice'],           # BOLT11 for user
            'payment_hash': invoice_data['payment_hash'], # Unique ID
            'payment_index': invoice_data['index'],       # REQUIRED for monitoring
            'amount': 1000,
            'status': 'pending'
        }
        
        # 2. Show invoice to user
        print(f"Pay this: {payment_record['invoice']}")
        
        # 3. Monitor payment completion
        payment_index = payment_record['payment_index']
        
        while True:
            # Check payment status using correct endpoint
            response = requests.get(f"http://localhost:5393/v1/node/payment?index={payment_index}")
            
            if response.status_code == 200:
                payment_data = response.json()
                payment = payment_data['payment']
                
                # CORRECT: Check for 'completed' status
                if payment['status'] == 'completed':
                    print(f"🎉 Payment received! Amount: {payment['amount']} sats")
                    # Update your database: status = 'completed'
                    break
                elif payment['status'] == 'pending':
                    print("⏳ Still waiting...")
                    time.sleep(3)  # Check every 3 seconds
                else:
                    print(f"❌ Payment failed: {payment['status']}")
                    break
            else:
                print("Error checking payment status")
                break
```

### Web App Integration (Flask)

```python
@app.route('/create-invoice', methods=['POST'])
def create_invoice():
    response = requests.post("http://localhost:5393/v1/node/create_invoice", json=request.json)
    invoice_data = response.json()
    
    # CRITICAL: Store payment_index for monitoring
    # Save to your database: invoice_data['index']
    
    return {'invoice': invoice_data['invoice'], 'payment_index': invoice_data['index']}

@app.route('/check-payment/<payment_index>')
def check_payment_status(payment_index):
    try:
        response = requests.get(f'http://localhost:5393/v1/node/payment?index={payment_index}')
        
        if response.status_code == 200:
            payment = response.json()['payment']
            
            # CRITICAL: Check for 'completed' not 'settled'
            return {
                'paid': payment['status'] == 'completed',
                'status': payment['status'],
                'amount': payment['amount']
            }
        else:
            return {'error': 'Payment not found'}, 404
            
    except Exception as e:
        return {'error': str(e)}, 500
```

### Database Schema Recommendations

```sql
-- Store these fields when creating invoices
CREATE TABLE lightning_payments (
    id SERIAL PRIMARY KEY,
    invoice TEXT NOT NULL,           -- BOLT11 string
    payment_hash TEXT NOT NULL,      -- Unique payment identifier  
    payment_index TEXT NOT NULL,     -- REQUIRED for status checking
    amount_sats INTEGER NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'pending',  -- pending, completed, failed
    created_at TIMESTAMP DEFAULT NOW(),
    finalized_at TIMESTAMP,
    
    UNIQUE(payment_index)
);
```

**📁 See `examples/correct_payment_flow.py` for complete, tested examples.**

## API Reference

### LexeManager Class

#### Constructor
```python
from lexe_wrapper import LexeManager

LexeManager(client_credentials=None, port=5393)
```
- `client_credentials`: Base64 encoded credentials (uses `LEXE_CLIENT_CREDENTIALS` env var if None)
- `port`: Port for sidecar to listen on (default: 5393)

#### Methods

**`start_sidecar(wait_for_health=True, health_timeout=30)`**
- Downloads binary if needed, starts process, optionally waits for health check
- Returns: `bool` - True if started successfully

**`start_for_webapp(health_timeout=30)`**
- Web app specific startup with robust error handling
- Returns: `bool` - True if started successfully
- Raises: `RuntimeError` if startup fails

**`stop_sidecar()`**
- Gracefully stops the sidecar process
- Returns: `bool` - True if stopped successfully

**`check_health()`**
- Checks if sidecar is responding to health checks
- Returns: `bool` - True if healthy

**`ensure_running()`**
- Ensures sidecar is running and healthy (great for health check endpoints)
- Returns: `bool` - True if running and healthy

**`restart_if_needed()`**
- Restarts sidecar if not running or unhealthy
- Returns: `bool` - True if now running and healthy

**`get_node_info()`**
- Gets node information from Lexe API
- Returns: `dict` - Node information including balance, channels, etc.

**`is_running()`**
- Checks if the sidecar process is currently running
- Returns: `bool` - True if running

## CLI Reference

The package includes a command-line interface for testing and development:

```bash
# Using the installed package
python -m lexe_wrapper <command> [options]

# Or directly (if you cloned the repo)
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

## Web App Integration (Long-Lived Connections)

The wrapper is specifically designed to support long-lived connections for web applications. Here's how to integrate it:

### Flask Example

```python
from flask import Flask, jsonify, request
from lexe_manager import LexeManager
import requests
import atexit

app = Flask(__name__)

# Global Lexe manager instance
lexe_manager = None

def init_lexe():
    """Initialize Lexe sidecar when app starts"""
    global lexe_manager
    lexe_manager = LexeManager()
    
    try:
        # Use the web app specific startup method
        lexe_manager.start_for_webapp(health_timeout=30)
        print("✅ Lexe sidecar started successfully")
        return True
    except RuntimeError as e:
        print(f"❌ Failed to start Lexe: {e}")
        return False

def cleanup_lexe():
    """Clean shutdown when app stops"""
    global lexe_manager
    if lexe_manager:
        lexe_manager.stop_sidecar()
        print("🛑 Lexe sidecar stopped")

# Initialize Lexe when app starts
with app.app_context():
    if not init_lexe():
        exit(1)

# Register cleanup function
atexit.register(cleanup_lexe)

@app.route('/health')
def health_check():
    """App health check - includes Lexe status"""
    if lexe_manager and lexe_manager.ensure_running():
        return jsonify({"status": "healthy", "lexe": "connected"})
    else:
        return jsonify({"status": "degraded", "lexe": "disconnected"}), 503

@app.route('/node-info')
def node_info():
    """Get Lexe node information"""
    try:
        # Use direct API call (the whole point of this wrapper!)
        response = requests.get("http://localhost:5393/v1/node/node_info", timeout=10)
        response.raise_for_status()
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/create-invoice', methods=['POST'])
def create_invoice():
    """Create a Lightning invoice"""
    try:
        amount = request.json.get('amount', '1000')
        description = request.json.get('description', 'Payment')
        
        # Direct Lexe API usage
        response = requests.post("http://localhost:5393/v1/node/create_invoice", 
                               json={
                                   "amount": str(amount),
                                   "description": description
                               }, timeout=15)
        response.raise_for_status()
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/restart-lexe', methods=['POST'])
def restart_lexe():
    """Restart Lexe if having issues"""
    if lexe_manager and lexe_manager.restart_if_needed():
        return jsonify({"status": "restarted"})
    else:
        return jsonify({"error": "restart failed"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

### FastAPI Example

```python
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from lexe_manager import LexeManager
import requests

# Global Lexe manager
lexe_manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global lexe_manager
    lexe_manager = LexeManager()
    
    try:
        lexe_manager.start_for_webapp()
        print("✅ Lexe sidecar started")
        yield
    except RuntimeError as e:
        print(f"❌ Lexe startup failed: {e}")
        raise
    finally:
        # Shutdown
        if lexe_manager:
            lexe_manager.stop_sidecar()
            print("🛑 Lexe sidecar stopped")

app = FastAPI(lifespan=lifespan)

@app.get("/health")
def health_check():
    if lexe_manager and lexe_manager.ensure_running():
        return {"status": "healthy", "lexe": "connected"}
    raise HTTPException(503, "Lexe not available")

@app.post("/invoices")
def create_invoice(amount: int, description: str = "Payment"):
    try:
        response = requests.post("http://localhost:5393/v1/node/create_invoice",
                               json={"amount": str(amount), "description": description})
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise HTTPException(500, str(e))
```

### Complete Flask Example with Real-Time Monitoring

We've included a **production-ready Flask application** that demonstrates proper payment tracking:

```bash
# Run the complete example
python examples/flask_payment_app.py
```

This example includes:
- ✅ Correct use of `index` field for payment tracking
- ✅ Background thread monitoring for payment completion
- ✅ SQLite database for payment storage
- ✅ Web UI with real-time status updates
- ✅ Proper error handling and timeouts
- ✅ Clear documentation of the critical integration points

See [`examples/flask_payment_app.py`](examples/flask_payment_app.py) for the complete implementation.

### Web App Best Practices

1. **Startup Pattern**: Use `start_for_webapp()` during app initialization
2. **Health Monitoring**: Use `ensure_running()` in your health check endpoints
3. **Recovery**: Use `restart_if_needed()` for automatic recovery
4. **Shutdown**: Ensure `stop_sidecar()` is called when your app shuts down
5. **Direct API Usage**: Once started, use standard HTTP requests to `localhost:5393`
6. **Payment Tracking**: ALWAYS save the `index` field and use it for status checks

### Process Management for Production

```python
import signal
import sys
from lexe_manager import LexeManager

# Global manager for signal handlers
lexe_manager = None

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    global lexe_manager
    print("🔄 Received shutdown signal, stopping Lexe...")
    if lexe_manager:
        lexe_manager.stop_sidecar()
    sys.exit(0)

# Register signal handlers for graceful shutdown
signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
signal.signal(signal.SIGTERM, signal_handler)  # Docker/systemd stop

def main():
    global lexe_manager
    lexe_manager = LexeManager()
    
    # Start for long-lived operation
    lexe_manager.start_for_webapp()
    
    # Your web app code here
    # The sidecar stays running until explicitly stopped
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

## Package Structure

```
lexe-wrapper/
├── lexe_wrapper/           # Main package
│   ├── __init__.py        # Package exports LexeManager
│   ├── manager.py         # Core LexeManager class
│   └── __main__.py        # CLI entry point
├── examples/              # Usage examples
│   └── simple_usage.py    # Simple integration examples
├── setup.py              # Package installation
├── pyproject.toml        # Modern Python packaging
└── README.md             # This documentation
```

## Requirements

- Python 3.7+
- `requests` library (automatically installed as dependency)
- x86_64 Linux environment (where Lexe sidecar runs)
- Valid Lexe client credentials

## Contributing

Contributions are welcome! This is an open-source project and we encourage community involvement:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

**Code of Conduct:** Please be respectful and constructive in all interactions.

## License

**MIT License** - This project is free and open-source software. See the [LICENSE](LICENSE) file for full details.

Copyright (c) 2025 Mat Balez

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software.

## About

This package is designed to eliminate the friction in getting started with Lexe Bitcoin Lightning Network integration. The Lexe Sidecar API itself is excellent - this package just handles the setup complexity so you can focus on building great Lightning applications.

**Key Design Principles:**
- **Standard Python packaging** - Install with pip, import normally
- **Minimal dependencies** - Only requires `requests`
- **Clean API surface** - Simple import, clear methods
- **Production ready** - Proper error handling, logging, and lifecycle management
- **Direct API access** - No unnecessary abstraction over the Lexe Sidecar API

## Open Source & Legal

**📝 License:** This project is released under the [MIT License](LICENSE), making it free to use, modify, and distribute.

**⚖️ Disclaimer:** This is an **unofficial, community-developed wrapper** around the Lexe Sidecar SDK. It is **not officially associated with, endorsed by, or supported by Lexe**. This project was independently created to help Python developers integrate with Lexe's Lightning wallet services more easily.

**🔧 Open Source:** 
- **Source Code:** Available on GitHub for transparency and community contributions
- **Issues & Contributions:** Welcome! Please submit bug reports and feature requests
- **No Warranty:** Provided "as is" - please review the code and test thoroughly before production use

**🔗 Official Lexe Resources:**
- Official Lexe Website: [lexe.app](https://lexe.app)
- Official Lexe Sidecar SDK: [github.com/lexe-app/lexe-sidecar-sdk](https://github.com/lexe-app/lexe-sidecar-sdk)
- Lexe Documentation: Follow official Lexe channels for authoritative information

## Author

**Created and maintained by [Mat Balez](mailto:matbalez@gmail.com)**

This project was developed to help the Python community easily integrate Bitcoin Lightning Network payments using Lexe's excellent infrastructure, with a focus on eliminating common setup friction points.