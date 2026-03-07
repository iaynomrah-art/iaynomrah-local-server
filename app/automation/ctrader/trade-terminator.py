import re
import time

def terminate_trade(page, symbol: str):
    print(f"\n👀 Monitoring started for {symbol}...")

    def parse_balance(text: str) -> float:
        # Strip out new lines to make it a single string
        text = text.replace('\n', ' ')
        
        # Isolate just the balance part if both labels exist
        if "Balance:" in text and "Equity:" in text:
            # Get the substring between "Balance:" and "Equity:"
            text = text.split("Balance:")[1].split("Equity:")[0]
            
        # Strip all letters, spaces, and currency symbols, keep only numbers and decimals
        clean_string = re.sub(r'[^\d.]', '', text)
        if not clean_string:
            print(f"⚠️ Failed to parse balance from string: '{text}'")
            return 0.0
            
        return float(clean_string)

    def get_balance_locator():
        # First strategy: The exact hierarchy from the screenshot
        # A div that has a child div containing 'Balance:' exactly
        locs = [
            page.locator("div:has(> div:has-text('Balance:'))").last,
            # Fallback 1: Look for any container that has BOTH words to force it up the tree
            page.locator("div:has-text('Balance:'):has-text('Equity:')").last,
            # Fallback 2: Find the span containing Balance:, go up two parents
            page.locator("span:has-text('Balance:') >> xpath=../..").last,
            # Fallback 3: Find the word Balance:, go to the next sibling div
            page.locator("div:has-text('Balance:') + div").last
        ]
        
        for loc in locs:
            try:
                if loc.is_visible(timeout=1000):
                    text = loc.inner_text()
                    if parse_balance(text) > 0:
                        return loc
            except Exception:
                pass
                
        # If all fail, return the first one as fallback and hope for the best
        return locs[0]

    try:
        # 1. Grab Initial Balance
        balance_locator = get_balance_locator()
        
        initial_text = balance_locator.inner_text()
        print(f"DEBUG - Full Footer Text Captured: {initial_text}")
        
        initial_balance = parse_balance(initial_text)
        print(f"💰 Starting Balance: {initial_balance}")
        print(f"⏳ Waiting for balance to change from {initial_balance} to detect Take Profit / Stop Loss...")

        # 2. Poll for balance changes
        while True:
            # Wait 2 seconds between checks
            page.wait_for_timeout(2000)
            
            # Use inner_text() which automatically strips a lot of whitespace and invisible chars
            current_text = balance_locator.inner_text()
            current_balance = parse_balance(current_text)
            
            if current_balance != initial_balance:
                final_balance = current_balance
                break

        # 3. Evaluate the result
        print("\n🚨 Balance changed! Reacting immediately...")
        print("-" * 40)
        if final_balance > initial_balance:
            print(f"✅ SUCCESS: TAKE PROFIT HIT! (Balance increased to {final_balance})")
            result = "TAKE_PROFIT"
        else: # final_balance < initial_balance
            print(f"❌ SUCCESS: STOP LOSS HIT! (Balance decreased to {final_balance})")
            result = "STOP_LOSS"
        print("-" * 40)
        
        return {"success": True, "reason": f"Trade closed. Result: {result}", "warning": None}
    
    except Exception as e:
        print(f"Error monitoring close: {str(e)}")
        return {"success": False, "reason": str(e), "warning": None}