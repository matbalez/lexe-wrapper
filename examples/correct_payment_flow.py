#!/usr/bin/env python3
"""
CORRECTED Payment Flow - Based on Real Developer Feedback

This shows the exact, tested approach for Lightning payment monitoring
that works with the actual Lexe API responses.

CRITICAL FIXES:
1. Payment status is 'completed' NOT 'settled' 
2. Must store payment_index from invoice creation
3. Correct API endpoint usage
4. Complete response structure examples
5. Database schema recommendations
"""

from lexe_wrapper import LexeManager
import requests
import time
import json

def create_invoice_and_store_data(amount_sats, description):
    """
    Step 1: Create invoice and store essential data for payment monitoring
    
    IMPORTANT: You MUST store the 'index' field to check payment status later!
    """
    print(f"💰 Creating invoice for {amount_sats} sats...")
    
    with LexeManager() as lexe:
        lexe.start_sidecar()
        
        # Create invoice using standard Lexe API
        response = requests.post("http://localhost:5393/v1/node/create_invoice", json={
            "amount": str(amount_sats),
            "description": description,
            "expiration_secs": 3600  # 1 hour
        })
        
        if response.status_code != 200:
            print(f"❌ Failed to create invoice: {response.text}")
            return None
            
        invoice_data = response.json()
        print("✅ Invoice created successfully!")
        
        # CRITICAL: Store these fields in your database
        payment_record = {
            'invoice': invoice_data['invoice'],           # BOLT11 string to show user
            'payment_hash': invoice_data['payment_hash'], # Unique payment identifier  
            'payment_index': invoice_data['index'],       # REQUIRED for status checking
            'amount': amount_sats,
            'description': description,
            'created_at': time.time(),
            'status': 'pending'  # Your app's tracking
        }
        
        print(f"📋 Store these fields in your database:")
        print(json.dumps(payment_record, indent=2))
        print(f"\n⚡ Show this to user: {invoice_data['invoice']}")
        
        return payment_record

def check_payment_completion(payment_index):
    """
    Step 2: Check if payment is completed
    
    CORRECT endpoint: GET /v1/node/payment?index=<payment_index>
    CORRECT status value: 'completed' (NOT 'settled'!)
    """
    endpoint = f"http://localhost:5393/v1/node/payment?index={payment_index}"
    print(f"🔍 Checking payment status at: {endpoint}")
    
    try:
        response = requests.get(endpoint)
        if response.status_code != 200:
            print(f"❌ API request failed: {response.status_code}")
            return None
            
        # ACTUAL API RESPONSE STRUCTURE (from real testing):
        payment_data = response.json()
        payment = payment_data['payment']
        
        print("📊 Complete API response:")
        print(json.dumps(payment_data, indent=2))
        
        # CRITICAL: Check for 'completed' status (NOT 'settled')
        if payment['status'] == 'completed':
            print("🎉 PAYMENT COMPLETED!")
            print(f"💰 Amount received: {payment['amount']} sats")
            print(f"💸 Fees paid: {payment['fees']} sats")  
            print(f"📅 Completed at: {payment['finalized_at']}")
            return True
        elif payment['status'] == 'pending':
            print("⏳ Payment still pending...")
            return False
        elif payment['status'] in ['failed', 'cancelled']:
            print(f"❌ Payment failed: {payment['status']}")
            return False
        else:
            print(f"⚠️  Unknown status: {payment['status']}")
            return False
            
    except Exception as e:
        print(f"💥 Error checking payment: {e}")
        return None

def wait_for_payment_completion(payment_index, timeout_seconds=300):
    """
    Step 3: Poll for payment completion with timeout
    
    This is the pattern your web app should use for automatic payment detection.
    """
    print(f"⏳ Monitoring payment for up to {timeout_seconds} seconds...")
    start_time = time.time()
    
    while time.time() - start_time < timeout_seconds:
        result = check_payment_completion(payment_index)
        
        if result is True:
            return True  # Payment completed!
        elif result is False:
            time.sleep(3)  # Check every 3 seconds
            continue
        else:
            # Error occurred
            print("💥 Error during monitoring, stopping...")
            return False
    
    print(f"⏰ Timeout reached after {timeout_seconds} seconds")
    return False

# Web App Integration Example
def web_app_payment_flow():
    """
    Complete example for web applications
    """
    print("\n🌐 WEB APP INTEGRATION EXAMPLE")
    print("=" * 50)
    
    # 1. Create invoice (when user clicks "Pay with Lightning")
    payment_record = create_invoice_and_store_data(1000, "Premium subscription")
    
    if not payment_record:
        return
    
    # 2. Show invoice to user
    bolt11 = payment_record['invoice']
    print(f"\n💳 Show user this invoice: {bolt11}")
    print("👆 User scans QR code or copies invoice to their Lightning wallet")
    
    # 3. In your web app, poll for completion (background task or AJAX)
    print(f"\n🔄 Your web app should poll this endpoint:")
    print(f"GET /check-payment/{payment_record['payment_index']}")
    
    # 4. Example Flask route
    print(f"\n🐍 Flask route example:")
    print(f"""
@app.route('/check-payment/<payment_index>')  
def check_payment_status(payment_index):
    try:
        response = requests.get(f'http://localhost:5393/v1/node/payment?index={{payment_index}}')
        if response.status_code == 200:
            payment = response.json()['payment']
            
            # CRITICAL: Check for 'completed' not 'settled'!
            if payment['status'] == 'completed':
                # Update your database
                # Send success response to frontend
                return {{'paid': True, 'amount': payment['amount'], 'finalized_at': payment['finalized_at']}}
            elif payment['status'] == 'pending':
                return {{'paid': False, 'status': 'waiting'}}
            else:
                return {{'paid': False, 'status': payment['status']}}
        else:
            return {{'error': 'Payment not found'}}, 404
    except Exception as e:
        return {{'error': str(e)}}, 500
""")

# Database Schema Recommendation
def show_database_schema():
    """
    Recommended database fields for Lightning payments
    """
    print("\n🗄️  RECOMMENDED DATABASE SCHEMA")
    print("=" * 50)
    
    schema = """
CREATE TABLE lightning_payments (
    id SERIAL PRIMARY KEY,
    
    -- From invoice creation (store immediately)
    invoice TEXT NOT NULL,              -- BOLT11 string
    payment_hash TEXT NOT NULL,         -- Unique payment identifier
    payment_index TEXT NOT NULL,        -- REQUIRED for status checking
    
    -- Payment details
    amount_sats INTEGER NOT NULL,
    description TEXT,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    finalized_at TIMESTAMP,
    
    -- Status tracking (your app's state)
    status VARCHAR(20) DEFAULT 'pending',  -- pending, completed, failed, expired
    
    -- Optional: User tracking
    user_id INTEGER,
    
    -- API response data (JSON)
    api_response JSONB,
    
    UNIQUE(payment_index),
    INDEX(payment_hash),
    INDEX(user_id, status)
);
"""
    
    print(schema)
    print("\n✅ Critical fields to store from invoice creation:")
    print("  • payment_index - REQUIRED for status checking")  
    print("  • payment_hash - Unique identifier")
    print("  • invoice - BOLT11 string to show user")

if __name__ == "__main__":
    print("⚡ CORRECTED LIGHTNING PAYMENT FLOW")
    print("Based on real developer feedback and testing")
    print("=" * 60)
    
    # Show database recommendations first
    show_database_schema()
    
    # Show complete web app example
    web_app_payment_flow()
    
    # Show manual testing
    print(f"\n🧪 MANUAL TESTING")
    print("=" * 50)
    
    payment_record = create_invoice_and_store_data(500, "Test payment")
    if payment_record:
        print(f"\n💡 To test:")
        print(f"1. Pay this invoice: {payment_record['invoice'][:50]}...")
        print(f"2. Run: check_payment_completion('{payment_record['payment_index']}')")
        print(f"3. Status should change from 'pending' to 'completed'")
        
        # Demonstrate one status check
        print(f"\n🔍 Current status:")
        check_payment_completion(payment_record['payment_index'])