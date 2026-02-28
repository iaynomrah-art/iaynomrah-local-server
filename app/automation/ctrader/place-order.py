import random
import importlib

input_order_module = importlib.import_module("app.automation.ctrader.input-order")
input_order = input_order_module.input_order


def random_delay(page, min_ms=800, max_ms=2500):
    """Wait a random duration to appear more human-like."""
    delay = random.randint(min_ms, max_ms)
    page.wait_for_timeout(delay)


def place_order(page):
    """
    Clicks the 'Place order' button to execute the order that was previously filled.
    """
    try:
        print("Attempting to place order (clicking button)...")

        # Check for any warning/error messages near the order panel
        warning_text = None
        try:
            warning_el = page.locator(':text("The market is closed"), :text("Only pending orders are accepted"), :text("not available for trading"), :text("Insufficient funds")').first
            if warning_el.is_visible(timeout=1500):
                warning_text = warning_el.inner_text().strip()
                print(f"  ⚠ Warning detected: {warning_text}")
        except Exception:
            pass

        # Selectors for the Place order / Execute button
        selectors = [
            'button:has-text("Place order")',
            'button:has-text("Place Order")',
            'button:has-text("Execute")',
            '.place-order-button',
            'button.green:has-text("Buy")',
            'button.red:has-text("Sell")'
        ]
        
        execute_button = None
        for selector in selectors:
            btn = page.locator(selector).first
            if btn.is_visible():
                execute_button = btn
                break
        
        if execute_button:
            # Check if the button is disabled (multiple methods for cTrader's custom UI)
            is_disabled = False
            try:
                is_disabled = execute_button.is_disabled()
            except Exception:
                pass
            
            if not is_disabled:
                try:
                    btn_classes = execute_button.get_attribute("class") or ""
                    opacity = execute_button.evaluate("el => getComputedStyle(el).opacity")
                    pointer_events = execute_button.evaluate("el => getComputedStyle(el).pointerEvents")
                    aria_disabled = execute_button.get_attribute("aria-disabled")
                    
                    if ("disabled" in btn_classes.lower() or 
                        opacity == "0.5" or float(opacity or "1") < 0.7 or
                        pointer_events == "none" or
                        aria_disabled == "true"):
                        is_disabled = True
                except Exception:
                    pass
            
            # If we detected a critical warning, treat button as disabled
            if warning_text and ("market is closed" in warning_text.lower() or "not available" in warning_text.lower()):
                is_disabled = True

            if is_disabled:
                reason = warning_text or "Place order button is disabled (unknown reason)"
                print(f"  ✗ Place order button is DISABLED. Reason: {reason}")
                return {"success": False, "reason": reason, "warning": warning_text}

            print(f"Found execution button: {execute_button.inner_text()}")
            execute_button.click(timeout=5000)
            print("Clicked Place Order button.")
            
            random_delay(page, 1000, 2000)

            # Verification logic
            try:
                success_notification = page.locator('text=/Order|Position|Executed|Success/i').first
                success_notification.wait_for(state="visible", timeout=10000)
                print("Order confirmation detected in UI.")
                return {"success": True, "reason": None, "warning": warning_text}
            except:
                if not execute_button.is_visible():
                    print("Execution button disappeared, assuming order was placed.")
                    return {"success": True, "reason": None, "warning": warning_text}
                return {"success": True, "reason": None, "warning": warning_text}
        else:
            print("Error: Could not find 'Place order' or 'Execute' button.")
            return {"success": False, "reason": "Could not find 'Place order' or 'Execute' button", "warning": warning_text}

    except Exception as e:
        print(f"Error during order execution: {str(e)}")
        return {"success": False, "reason": str(e), "warning": None}




def full_place_order(page, purchase_type, order_amount, symbol, take_profit, stop_loss):
    """
    Places a new order by filling in the order form and clicking the submit button.
    (Full Cycle: Fill + Execute)
    """
    print(f"Running Full Cycle Order: {purchase_type} {order_amount} {symbol}")

    # Step 1: Fill in the order form
    result = input_order(page, purchase_type, order_amount, symbol, take_profit, stop_loss)
    
    # Handle both old bool and new dict returns
    if isinstance(result, dict):
        if not result.get("success"):
            print(f"Failed to fill order details: {result.get('reason')}")
            return result
    elif not result:
        print("Failed to fill order details.")
        return {"success": False, "reason": "Failed to fill order details", "warning": None}

    random_delay(page, 500, 1500)

    # Step 2: Execute the order
    return place_order(page)
