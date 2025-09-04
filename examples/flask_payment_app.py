#!/usr/bin/env python3
"""
Complete Flask Web App with Real-Time Payment Monitoring
This example demonstrates the correct way to track Lightning payments in a web application.

Key Points:
1. Uses the 'index' field from invoice creation (NOT payment_hash)
2. Implements proper polling to detect 'completed' status
3. Includes error handling and timeout management
4. Shows database storage pattern
"""

from flask import Flask, request, jsonify, render_template_string
from lexe_wrapper import LexeManager
import requests
import threading
import time
import sqlite3
import os
from datetime import datetime
from contextlib import contextmanager

app = Flask(__name__)

# Global Lexe manager instance
lexe_manager = None

# Initialize database
def init_database():
    """Create the payments table if it doesn't exist"""
    conn = sqlite3.connect('payments.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lightning_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            payment_index TEXT UNIQUE NOT NULL,
            invoice_string TEXT NOT NULL,
            amount_sats INTEGER NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            paid_at TIMESTAMP,
            metadata TEXT
        )
    ''')
    conn.commit()
    conn.close()

@contextmanager
def get_db():
    """Database connection context manager"""
    conn = sqlite3.connect('payments.db')
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_lexe():
    """Initialize Lexe sidecar when app starts"""
    global lexe_manager
    lexe_manager = LexeManager()
    
    try:
        lexe_manager.start_for_webapp(health_timeout=30)
        print("✅ Lexe sidecar started successfully")
        return True
    except RuntimeError as e:
        print(f"❌ Failed to start Lexe: {e}")
        return False

def monitor_payment(payment_index, timeout_seconds=600):
    """
    Background thread to monitor payment status
    THIS IS THE CRITICAL FUNCTION - it uses the INDEX to check status
    """
    print(f"🔍 Starting payment monitor for index: {payment_index}")
    
    timeout = time.time() + timeout_seconds
    
    while time.time() < timeout:
        try:
            # CRITICAL: Use the payment index to check status
            response = requests.get(
                f"http://localhost:5393/v1/node/payment?index={payment_index}",
                timeout=10
            )
            
            if response.status_code == 200:
                payment_data = response.json()
                # CRITICAL: Access the nested 'payment' object
                payment = payment_data['payment']  # The API returns nested structure!
                status = payment.get('status', 'unknown')
                
                # Check for completion (NOT 'settled'!)
                if status == 'completed':
                    # Payment received successfully
                    with get_db() as conn:
                        cursor = conn.cursor()
                        cursor.execute('''
                            UPDATE lightning_payments 
                            SET status = ?, paid_at = ? 
                            WHERE payment_index = ?
                        ''', ('completed', datetime.now(), payment_index))
                        conn.commit()
                    
                    print(f"✅ Payment {payment_index} completed: {payment.get('amount')} sats")
                    # Trigger any post-payment actions (webhooks, order fulfillment, etc.)
                    handle_successful_payment(payment_index, payment)
                    break
                    
                elif status in ['failed', 'cancelled']:
                    # Payment failed or was cancelled
                    with get_db() as conn:
                        cursor = conn.cursor()
                        cursor.execute('''
                            UPDATE lightning_payments 
                            SET status = ? 
                            WHERE payment_index = ?
                        ''', (status, payment_index))
                        conn.commit()
                    
                    print(f"❌ Payment {payment_index} {status}")
                    break
                    
        except requests.RequestException as e:
            print(f"⚠️ Error checking payment {payment_index}: {e}")
        
        # Poll every 2 seconds
        time.sleep(2)
    
    else:
        # Timeout reached
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE lightning_payments 
                SET status = 'expired' 
                WHERE payment_index = ?
            ''', (payment_index,))
            conn.commit()
        print(f"⏰ Payment {payment_index} timed out")

def handle_successful_payment(payment_index, payment_data):
    """
    Handle successful payment completion
    This is where you'd trigger order fulfillment, send emails, etc.
    """
    print(f"🎉 Processing successful payment {payment_index}")
    # Add your business logic here:
    # - Send confirmation email
    # - Update order status
    # - Trigger webhooks
    # - Generate download links
    # etc.

@app.route('/')
def home():
    """Simple homepage with payment form"""
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Lightning Payment Demo</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            .alert { padding: 10px; margin: 10px 0; border-radius: 5px; }
            .alert-warning { background-color: #fff3cd; border: 1px solid #ffc107; }
            .alert-success { background-color: #d4edda; border: 1px solid #28a745; }
            .payment-form { background: #f8f9fa; padding: 20px; border-radius: 5px; }
            input, button { padding: 10px; margin: 5px; }
            button { background: #007bff; color: white; border: none; cursor: pointer; }
            .invoice-display { background: #e9ecef; padding: 15px; border-radius: 5px; margin: 15px 0; }
            .status { font-weight: bold; }
            .pending { color: #ffc107; }
            .completed { color: #28a745; }
            .failed { color: #dc3545; }
        </style>
    </head>
    <body>
        <h1>⚡ Lightning Payment Demo</h1>
        
        <div class="alert alert-warning">
            <strong>🚨 Critical Integration Note:</strong><br>
            This demo shows the CORRECT way to track payments using the 'index' field.<br>
            Do NOT use payment_hash for status checking with Lexe!
        </div>
        
        <div class="payment-form">
            <h2>Create Lightning Invoice</h2>
            <input type="number" id="amount" placeholder="Amount (sats)" value="1000">
            <input type="text" id="description" placeholder="Description" value="Test payment">
            <button onclick="createInvoice()">Create Invoice</button>
        </div>
        
        <div id="result"></div>
        
        <script>
        async function createInvoice() {
            const amount = document.getElementById('amount').value;
            const description = document.getElementById('description').value;
            
            const response = await fetch('/api/create-invoice', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({amount, description})
            });
            
            const data = await response.json();
            
            if (data.success) {
                document.getElementById('result').innerHTML = `
                    <div class="invoice-display">
                        <h3>✅ Invoice Created</h3>
                        <p><strong>Amount:</strong> ${amount} sats</p>
                        <p><strong>Payment Index:</strong> ${data.payment_index}</p>
                        <p><strong>Invoice:</strong></p>
                        <textarea style="width:100%; height:100px;">${data.invoice}</textarea>
                        <p class="status ${data.status}">Status: ${data.status}</p>
                        <button onclick="checkStatus('${data.payment_index}')">Check Status</button>
                    </div>
                `;
                
                // Auto-check status every 3 seconds
                const interval = setInterval(async () => {
                    const status = await checkStatusSilent(data.payment_index);
                    if (status !== 'pending') {
                        clearInterval(interval);
                    }
                }, 3000);
            } else {
                document.getElementById('result').innerHTML = `
                    <div class="alert alert-danger">Error: ${data.error}</div>
                `;
            }
        }
        
        async function checkStatus(paymentIndex) {
            const response = await fetch(`/api/payment-status/${paymentIndex}`);
            const data = await response.json();
            
            const statusElement = document.querySelector('.status');
            statusElement.className = `status ${data.status}`;
            statusElement.textContent = `Status: ${data.status}`;
            
            if (data.status === 'completed') {
                statusElement.textContent += ' ✅ Payment received!';
            }
        }
        
        async function checkStatusSilent(paymentIndex) {
            const response = await fetch(`/api/payment-status/${paymentIndex}`);
            const data = await response.json();
            
            const statusElement = document.querySelector('.status');
            if (statusElement) {
                statusElement.className = `status ${data.status}`;
                statusElement.textContent = `Status: ${data.status}`;
                
                if (data.status === 'completed') {
                    statusElement.textContent += ' ✅ Payment received!';
                }
            }
            
            return data.status;
        }
        </script>
    </body>
    </html>
    ''')

@app.route('/api/create-invoice', methods=['POST'])
def create_invoice():
    """
    Create a Lightning invoice
    CRITICAL: Returns the 'index' field that must be used for tracking
    """
    try:
        data = request.json
        amount = data.get('amount', '1000')
        description = data.get('description', 'Payment')
        
        # Create invoice via Lexe API
        response = requests.post(
            "http://localhost:5393/v1/node/create_invoice",
            json={
                "amount": str(amount),
                "description": description,
                "expiration_secs": 600  # 10 minutes
            },
            timeout=15
        )
        
        if response.status_code == 200:
            invoice_data = response.json()
            
            # CRITICAL: Extract the INDEX for payment tracking
            payment_index = invoice_data['index']  # THIS IS WHAT WE NEED!
            invoice_string = invoice_data['invoice']
            
            # Store in database
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO lightning_payments 
                    (payment_index, invoice_string, amount_sats, description)
                    VALUES (?, ?, ?, ?)
                ''', (payment_index, invoice_string, int(amount), description))
                conn.commit()
            
            # Start background monitoring thread
            monitor_thread = threading.Thread(
                target=monitor_payment,
                args=(payment_index,),
                daemon=True
            )
            monitor_thread.start()
            
            return jsonify({
                'success': True,
                'payment_index': payment_index,  # Return this for frontend tracking
                'invoice': invoice_string,
                'amount': amount,
                'status': 'pending'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to create invoice'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/payment-status/<payment_index>')
def payment_status(payment_index):
    """Get the current status of a payment by its index"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM lightning_payments WHERE payment_index = ?',
                (payment_index,)
            )
            payment = cursor.fetchone()
            
            if payment:
                return jsonify({
                    'payment_index': payment['payment_index'],
                    'status': payment['status'],
                    'amount': payment['amount_sats'],
                    'created_at': payment['created_at'],
                    'paid_at': payment['paid_at']
                })
            else:
                return jsonify({'error': 'Payment not found'}), 404
                
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/payments')
def list_payments():
    """List all payments"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM lightning_payments ORDER BY created_at DESC LIMIT 50'
            )
            payments = cursor.fetchall()
            
            return jsonify([dict(p) for p in payments])
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    if lexe_manager and lexe_manager.ensure_running():
        return jsonify({"status": "healthy", "lexe": "connected"})
    else:
        return jsonify({"status": "degraded", "lexe": "disconnected"}), 503

if __name__ == '__main__':
    # Initialize database
    init_database()
    
    # Initialize Lexe
    if not init_lexe():
        print("Failed to start Lexe sidecar. Exiting.")
        exit(1)
    
    try:
        # Run Flask app
        app.run(host='0.0.0.0', port=5000, debug=False)
    finally:
        # Clean shutdown
        if lexe_manager:
            lexe_manager.stop_sidecar()
            print("🛑 Lexe sidecar stopped")