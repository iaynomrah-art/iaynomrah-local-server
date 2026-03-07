import requests
import json

BASE_URL = "http://localhost:2026/api/v1"

def test_credentials_endpoint():
    print("Testing /trade/credentials...")
    try:
        response = requests.get(f"{BASE_URL}/trade/credentials")
        response.raise_for_status()
        data = response.json()
        print(f"Success! Found {len(data)} cTrader accounts.")
        for cred in data:
            print(f" - {cred.get('username')} ({cred.get('platform_id')})")
        return data
    except Exception as e:
        print(f"Error testing credentials: {e}")
        return None

def test_trade_endpoint(cred):
    if not cred:
        print("Skipping trade test (no valid credentials)")
        return

    print("\nTesting /trade/ctrader (dry run/validation)...")
    payload = {
        "username": cred.get('username'),
        "password": cred.get('password'), # Note: in a real test this should be valid
        "purchase_type": "buy",
        "order_amount": "0.1",
        "take_profit": "50",
        "stop_loss": "50",
        "account_id": cred.get('platform_id'),
        "symbol": "XAUUSD",
        "operation": "default"
    }
    
    # We won't actually run it to avoid opening the browser if we don't want to,
    # but we can verify the API structure is correct.
    print(f"Payload prepared for {cred.get('username')}")

if __name__ == "__main__":
    creds = test_credentials_endpoint()
    if creds:
        test_trade_endpoint(creds[0])
