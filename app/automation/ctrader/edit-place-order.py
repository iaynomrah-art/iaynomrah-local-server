import random
import importlib

input_order_module = importlib.import_module("app.automation.ctrader.input-order")
input_order = input_order_module.input_order


def random_delay(page, min_ms=800, max_ms=2500):
    """Wait a random duration to appear more human-like."""
    delay = random.randint(min_ms, max_ms)
    page.wait_for_timeout(delay)


def edit_place_order(page, purchase_type, order_amount, symbol, take_profit, stop_loss):
    """
    Edits an existing pending order by modifying the order form fields
    and then confirming the changes.
    """
    print(f"Editing order: {purchase_type} {order_amount} {symbol}")

    random_delay(page, 500, 1500)

    # Look for the existing order to edit (click on the pending order row)
    order_row = page.locator(f'text="{symbol}"').first
    if order_row.is_visible():
        order_row.dblclick()
        print(f"Double-clicked on existing order for {symbol}")
    else:
        print(f"Warning: Could not find existing order for {symbol}")

    random_delay(page, 800, 1800)

    # Fill in the updated order form
    input_order(page, purchase_type, order_amount, symbol, take_profit, stop_loss)

    random_delay(page, 500, 1500)

    # Click the modify/confirm button
    modify_button = page.locator('button:has-text("Modify")').first
    if not modify_button.is_visible():
        modify_button = page.locator('button:has-text("Confirm")').first
    if not modify_button.is_visible():
        modify_button = page.locator('button:has-text("Apply")').first

    if modify_button.is_visible():
        modify_button.click()
        print("Clicked Modify / Confirm button")
    else:
        print("Warning: Could not find Modify or Confirm button")

    random_delay(page, 1000, 2500)
    print("Edit place order complete.")
