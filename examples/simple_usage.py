#!/usr/bin/env python3
"""
Simple usage example for lexe-wrapper package.

This demonstrates the easiest way to get started with Lexe Lightning integration.
"""

from lexe_wrapper import LexeManager
import requests

def main():
    print("🚀 Simple Lexe Wrapper Example")
    print("=" * 40)
    
    # Method 1: Context manager (automatic cleanup)
    print("\n📦 Method 1: Context Manager")
    with LexeManager() as lexe:
        lexe.start_sidecar()
        print(f"✅ Lexe ready at {lexe.base_url}")
        
        # Get node info using direct API
        response = requests.get(f"{lexe.base_url}/v1/node/node_info")
        node_info = response.json()
        print(f"💰 Balance: {node_info['balance']} sats")
    
    print("🛑 Sidecar stopped automatically")
    
    # Method 2: Manual management
    print("\n🔧 Method 2: Manual Management")
    lexe = LexeManager()
    
    try:
        lexe.start_for_webapp()  # Web app ready startup
        print("✅ Web app integration ready")
        
        # Create an invoice using direct API
        invoice_response = requests.post(f"{lexe.base_url}/v1/node/create_invoice", json={
            "amount": "100",
            "description": "Example payment"
        })
        invoice = invoice_response.json()
        print(f"🧾 Created invoice: {invoice.get('invoice', 'Success')[:50]}...")
        
    finally:
        lexe.stop_sidecar()
        print("🛑 Sidecar stopped manually")
    
    print("\n🎉 Example complete!")

if __name__ == "__main__":
    main()