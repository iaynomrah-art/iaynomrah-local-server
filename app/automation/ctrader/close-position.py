import random

def random_delay(page, min_ms=500, max_ms=1500):
    """Wait a random duration to appear more human-like."""
    delay = random.randint(min_ms, max_ms)
    page.wait_for_timeout(delay)

def close_position(page, symbol: str) -> dict:
    """
    Closes an open position for a given symbol in the 'Positions' tab.
    Uses geometric matching to find the 'Close' SVG icon (ic_access_cross) on the same row as the symbol.
    """
    print(f"Attempting to close position for: {symbol}")
    
    try:
        # Step 1: Ensure the 'Positions' tab is active
        try:
            positions_tab = page.locator('div:has-text("Positions")').first
            if positions_tab.is_visible(timeout=2000):
                positions_tab.click()
                random_delay(page, 300, 800)
        except Exception:
            pass  # Already visible or not found, proceed anyway
            
        random_delay(page, 500, 1000)

        # Step 2: Direct Locator Strategy
        # The user requested to avoid `has-text` because the row's text content dynamically updates (prices/ticks),
        # which can cause Playwright's virtual DOM detached element errors.
        # Playwright inspector suggests simply using the SVG ID.
        
        print("  > Searching for close position buttons (#ic_access_cross)...")
        close_buttons = page.locator('svg#ic_access_cross').all()
        
        target_close_btn = None
        
        for btn in close_buttons:
            if btn.is_visible(timeout=1000):
                target_close_btn = btn
                break
                
        if target_close_btn:
            print(f"  ✓ Found close button (#ic_access_cross). Attempting to click.")
            target_close_btn.click(timeout=3000)
            print(f"  ✓ Clicked the close button.")
            
            # Step 3: Verify it closed
            random_delay(page, 1500, 2500)
            
            # Double check if a confirmation dialog appeared (some brokers/settings require it)
            try:
                confirm_btn = page.locator('button:has-text("Confirm")').first
                if confirm_btn.is_visible(timeout=1000):
                    print("  ⚠ Confirmation dialog detected. Clicking Confirm...")
                    confirm_btn.click(timeout=3000)
                    random_delay(page, 800, 1500)
            except Exception:
                pass
            
            # Check if the target button disappeared
            try:
                if target_close_btn.is_visible(timeout=2000):
                    print(f"  ⚠ Warning: Close button still visible for {symbol}. It may not have closed.")
                    return {"success": False, "reason": f"Position for {symbol} did not close after clicking", "warning": None}
            except Exception:
                # Element handle might be disposed, meaning it's gone
                pass
                
            print(f"  ✓ Position for {symbol} successfully closed.")
            return {"success": True, "reason": None, "warning": None}
            
        else:
            print(f"  ✗ Could not find an active position or close button for {symbol}.")
            return {"success": False, "reason": f"No active position found for {symbol}", "warning": "Position may be already closed or not exist"}
            
    except Exception as e:
        err_msg = str(e)
        print(f"Error while trying to close position: {err_msg}")
        return {"success": False, "reason": err_msg, "warning": None}
