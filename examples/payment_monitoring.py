#!/usr/bin/env python3
"""
Complete Lightning payment monitoring example.

This demonstrates the full payment lifecycle:
1. Create invoice
2. Monitor for payment
3. Confirm payment completion
"""

from lexe_wrapper import LexeManager
import requests
import time
import json

def create_and_monitor_payment(amount_sats, description, timeout=300):
    """
    Create a Lightning invoice and monitor until payment is received.
    
    Args:
        amount_sats: Payment amount in satoshis
        description: Payment description  
        timeout: Maximum time to wait for payment (seconds)
        
    Returns:
        (success, payment_data) tuple
    """
    with LexeManager() as lexe:
        lexe.start_sidecar()
        
        # Step 1: Create Lightning invoice
        print(f"💰 Creating invoice for {amount_sats} sats...")
        invoice_response = requests.post("http://localhost:5393/v1/node/create_invoice", json={
            "amount": str(amount_sats),
            "description": description,
            "expiration_secs": 3600  # 1 hour expiration
        })
        
        if invoice_response.status_code != 200:
            print(f"❌ Invoice creation failed: {invoice_response.text}")
            return False, None
            
        invoice_data = invoice_response.json()
        payment_index = invoice_data['index']  # CRITICAL: Store this for payment monitoring!
        payment_hash = invoice_data.get('payment_hash')  # Also store for your database
        bolt11 = invoice_data['invoice']
        
        print(f"✅ Invoice created!")
        print(f"⚡ BOLT11: {bolt11}")
        print(f"🔍 Payment index: {payment_index}")
        print(f"⏳ Waiting for payment (timeout: {timeout}s)...")
        
        # Step 2: Monitor payment status
        return wait_for_payment(payment_index, timeout)

def wait_for_payment(payment_index, timeout=300):
    """
    Monitor a payment until completion or timeout.
    
    Args:
        payment_index: Payment index returned from invoice creation
        timeout: Maximum time to wait (seconds)
        
    Returns:
        (success, payment_data) tuple
    """
    endpoint = f"http://localhost:5393/v1/node/payment?index={payment_index}"
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(endpoint)
            if response.status_code == 200:
                payment_data = response.json()
                payment = payment_data['payment']
                
                status = payment['status']
                print(f"🔍 Payment status: {status} - {payment.get('status_msg', '')}")
                
                # Check for payment completion - API returns 'completed' when payment succeeds
                if status == 'completed':
                    print(f"🎉 Payment received!")
                    print(f"💸 Amount: {payment['amount']} sats")
                    print(f"📅 Finalized at: {payment.get('finalized_at')}")
                    return True, payment_data
                    
                elif status == 'failed' or status == 'cancelled':
                    print(f"❌ Payment failed: {payment.get('status_msg')}")
                    return False, payment_data
                    
        except Exception as e:
            print(f"⚠️  Error checking payment: {e}")
            
        time.sleep(2)  # Check every 2 seconds
    
    print(f"⏰ Payment monitoring timed out after {timeout} seconds")
    return False, None

def check_payment_status(payment_index):
    """
    Check the current status of a payment (one-time check).
    
    Args:
        payment_index: Payment index from invoice creation
        
    Returns:
        payment_data dict or None if error
    """
    try:
        response = requests.get(f"http://localhost:5393/v1/node/payment?index={payment_index}")
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error checking payment status: {e}")
    return None

# Example usage patterns
if __name__ == "__main__":
    print("⚡ Lightning Payment Monitoring Examples")
    print("=" * 50)
    
    # Example 1: Simple payment monitoring
    print("\n📋 Example 1: Create invoice and wait for payment")
    success, payment_data = create_and_monitor_payment(
        amount_sats=1000,
        description="Example payment",
        timeout=30  # Short timeout for demo
    )
    
    if success:
        print("✅ Payment completed successfully!")
    else:
        print("❌ Payment not received within timeout")
    
    # Example 2: Manual status checking
    print("\n📋 Example 2: Manual payment status checking")
    with LexeManager() as lexe:
        lexe.start_sidecar()
        
        # Create invoice
        invoice_response = requests.post("http://localhost:5393/v1/node/create_invoice", json={
            "amount": "500",
            "description": "Manual check example",
            "expiration_secs": 3600
        })
        
        if invoice_response.status_code == 200:
            invoice_data = invoice_response.json()
            payment_index = invoice_data['index']
            
            print(f"📝 Invoice created with index: {payment_index}")
            print(f"💳 Pay this invoice: {invoice_data['invoice']}")
            
            # Check status once
            status_data = check_payment_status(payment_index)
            if status_data:
                payment = status_data['payment']
                print(f"📊 Current status: {payment['status']}")
                print(f"💰 Amount: {payment['amount']} sats")
                print(f"📝 Description: {invoice_data['description']}")
                
                # Show how to integrate into web app
                print(f"\n🌐 Web App Integration Example:")
                print(f"```python")
                print(f"@app.route('/check-payment/<payment_index>')")
                print(f"def check_payment_status(payment_index):")
                print(f"    response = requests.get(f'http://localhost:5393/v1/node/payment?index={{payment_index}}')")
                print(f"    if response.status_code == 200:")
                print(f"        payment = response.json()['payment']")
                print(f"        return {{'status': payment['status'], 'paid': payment['status'] == 'settled'}}")
                print(f"    return {{'error': 'Payment not found'}}")
                print(f"```")