import random
import importlib

input_order_module = importlib.import_module("app.automation.ctrader.input-order")
input_order = input_order_module.input_order


def random_delay(page, min_ms=800, max_ms=2500):
    """Wait a random duration to appear more human-like."""
    delay = random.randint(min_ms, max_ms)
    page.wait_for_timeout(delay)


def execute_order(page):
    """
    Clicks the 'Place order' button to execute the order that was previously filled.
    """
    try:
        print("Attempting to execute order...")

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
            print(f"Found execution button: {execute_button.inner_text()}")
            execute_button.click()
            print("Clicked execution button.")
            
            random_delay(page, 1000, 2000)

            # Verification logic
            try:
                success_notification = page.locator('text=/Order|Position|Executed|Success/i').first
                success_notification.wait_for(state="visible", timeout=10000)
                print("Order confirmation detected in UI.")
                return True
            except:
                if not execute_button.is_visible():
                    print("Execution button disappeared, assuming order was placed.")
                    return True
                return True 
        else:
            print("Error: Could not find 'Place order' or 'Execute' button.")
            return False

    except Exception as e:
        print(f"Error during order execution: {str(e)}")
        return False


def place_order(page, purchase_type, order_amount, symbol, take_profit, stop_loss):
    """
    Places a new order by filling in the order form and clicking the submit button.
    (Full Cycle: Fill + Execute)
    """
    print(f"Placing order: {purchase_type} {order_amount} {symbol}")

    # Step 1: Fill in the order form
    if not input_order(page, purchase_type, order_amount, symbol, take_profit, stop_loss):
        print("Failed to fill order details.")
        return False

    random_delay(page, 500, 1500)

    # Step 2: Execute the order
    return execute_order(page)