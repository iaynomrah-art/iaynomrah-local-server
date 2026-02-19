import random
import importlib

input_order_module = importlib.import_module("app.automation.ctrader.input-order")
input_order = input_order_module.input_order


def random_delay(page, min_ms=800, max_ms=2500):
    """Wait a random duration to appear more human-like."""
    delay = random.randint(min_ms, max_ms)
    page.wait_for_timeout(delay)


def place_order(page, purchase_type, order_amount, symbol, take_profit, stop_loss):
    """
    Places a new order by filling in the order form and clicking the submit button.
    """
    print(f"Placing order: {purchase_type} {order_amount} {symbol}")

    # Fill in the order form
    input_order(page, purchase_type, order_amount, symbol, take_profit, stop_loss)

    random_delay(page, 500, 1500)

    # Click the place order / execute button
    execute_button = page.locator('button:has-text("Execute")').first
    if not execute_button.is_visible():
        execute_button = page.locator('button:has-text("Place Order")').first

    if execute_button.is_visible():
        execute_button.click()
        print("Clicked Execute / Place Order button")
    else:
        print("Warning: Could not find Execute or Place Order button")

    random_delay(page, 1000, 2500)
    print("Place order complete.")
