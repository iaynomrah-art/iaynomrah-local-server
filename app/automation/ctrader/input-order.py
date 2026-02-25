import random

<<<<<<< Updated upstream
=======

>>>>>>> Stashed changes
def random_delay(page, min_ms=800, max_ms=2500):
    """Wait a random duration to appear more human-like."""
    delay = random.randint(min_ms, max_ms)
    page.wait_for_timeout(delay)
<<<<<<< Updated upstream
=======


def _ensure_field_enabled_and_fill(page, label_text, input_placeholder, value, timeout=5000):
    """
    Robustly enable and fill a Stop Loss or Take Profit field on cTrader.

    Strategy:
      1. Try to find the input field directly. If it's visible and interactable, fill it.
      2. If the input is NOT found or NOT visible, click the label text to toggle it on.
      3. Wait explicitly until the input field becomes visible.
      4. Fill the value.

    This avoids relying on SVG checkbox state, dynamic CSS classes, or standard
    checkbox attributes — none of which are reliable in cTrader's custom UI.
    """
    input_locator = page.locator(f'input[placeholder="{input_placeholder}"]').first

    # --- Attempt 1: Input already visible ---
    try:
        if input_locator.is_visible(timeout=1000):
            input_locator.click()
            page.keyboard.press("Control+A")
            page.keyboard.press("Backspace")
            input_locator.fill(str(value))
            print(f"  ✓ {label_text} field was already visible — filled with {value}")
            return True
    except Exception:
        pass  # Field not visible yet, proceed to toggle

    # --- Attempt 2: Click the label text to toggle the field on ---
    print(f"  ⏳ {label_text} field not visible — clicking label to enable...")

    # Use get_by_text with exact match on the label to avoid clicking wrong elements.
    # cTrader renders the label as plain text inside a custom component row.
    label_locator = page.get_by_text(label_text, exact=True).first

    try:
        label_locator.wait_for(state="visible", timeout=timeout)
        label_locator.click()
        print(f"  ✓ Clicked '{label_text}' label")
    except Exception as e:
        print(f"  ✗ Could not find or click '{label_text}' label: {e}")
        return False

    random_delay(page, 300, 600)

    # --- Attempt 3: Wait for the input to appear after toggling ---
    try:
        input_locator.wait_for(state="visible", timeout=timeout)
        input_locator.click()
        page.keyboard.press("Control+A")
        page.keyboard.press("Backspace")
        input_locator.fill(str(value))
        print(f"  ✓ {label_text} field appeared after toggle — filled with {value}")
        return True
    except Exception as e:
        print(f"  ✗ {label_text} input did not become visible after toggle: {e}")
        return False

>>>>>>> Stashed changes

def input_order(page, purchase_type, order_amount, symbol, take_profit, stop_loss):
    """
    Fills in the order form fields: symbol, purchase type (buy/sell),
    order amount, take profit, and stop loss.
    """
    try:
        print(f"Inputting order: {purchase_type} {order_amount} {symbol} TP:{take_profit} SL:{stop_loss}")

        random_delay(page, 500, 1500)

        # 1. Search and select the symbol
        symbol_input = page.locator('input[placeholder="Search"]').first
        if symbol_input.is_visible():
            symbol_input.click()
            page.keyboard.press("Control+A")
            page.keyboard.press("Backspace")
            symbol_input.fill(symbol)
            print(f"Searched for symbol: {symbol}")
            random_delay(page, 1000, 2000)

            # Click the symbol from search results
            symbol_result = page.locator(f'.symbol-name:has-text("{symbol}")').first
            if not symbol_result.is_visible():
                symbol_result = page.locator(f'text="{symbol}"').first

            if symbol_result.is_visible():
                symbol_result.click()
                print(f"Selected symbol: {symbol}")

        random_delay(page, 500, 1200)

        # 2. Select buy or sell
        if purchase_type.lower() == "buy":
            buy_button = page.locator('button.buy:has-text("Buy"), button:has-text("Buy")').first
            if buy_button.is_visible():
                buy_button.click()
                print("Selected: Buy")
        elif purchase_type.lower() == "sell":
            sell_button = page.locator('button.sell:has-text("Sell"), button:has-text("Sell")').first
            if sell_button.is_visible():
                sell_button.click()
                print("Selected: Sell")

        random_delay(page, 400, 1000)

        # 3. Fill in the order amount/volume
<<<<<<< Updated upstream
        # Attempt to find the quantity input reliably
        amount_input = page.locator('div:has-text("Quantity") + div input, .quantity-input input, input[aria-label="Volume"]').first
        if not amount_input.is_visible():
            amount_input = page.locator('input[type="text"]').nth(1) # Fallback
=======
        amount_input = page.locator('input[type="text"]').nth(1)
        quantity_input = page.locator('div:has-text("Quantity") + div input, .quantity-input input').first
        if quantity_input.is_visible():
            amount_input = quantity_input
>>>>>>> Stashed changes

        if amount_input.is_visible():
            amount_input.click()
            page.keyboard.press("Control+A")
            page.keyboard.press("Backspace")
            amount_input.fill(str(order_amount))
            page.keyboard.press("Enter") # Lock in the value
            print(f"Entered order amount: {order_amount}")

        random_delay(page, 400, 1000)

        # 4. Fill in take profit (robust toggle + fill)
        if take_profit:
<<<<<<< Updated upstream
            # Locate the exact text element for Take profit
            tp_label = page.locator('div:text-is("Take profit"), div:text-is("Take Profit")').first
            
            if tp_label.is_visible():
                # Go up one level to the parent container
                tp_parent = tp_label.locator('..')
                
                # Check if the checkmark SVG is currently visible inside this container
                is_checked = tp_parent.locator('svg#ic_checkmark, svg[id*="checkmark"]').is_visible()
                
                if not is_checked:
                    print("Take Profit is OFF. Clicking to enable...")
                    tp_parent.click()
                    random_delay(page, 500, 1000)
                else:
                    print("Take Profit is already ON. Skipping toggle.")

            # Now find the input box for TP and fill it
            tp_input = page.locator('input[placeholder="T/P"], .tp-input input, input[aria-label="Take Profit"]').first
            if tp_input.is_visible():
                tp_input.click()
                page.keyboard.press("Control+A")
                page.keyboard.press("Backspace")
                tp_input.fill(str(take_profit))
                page.keyboard.press("Enter")
                print(f"Entered take profit: {take_profit}")
=======
            print("Handling Take Profit...")
            _ensure_field_enabled_and_fill(page, "Take profit", "T/P", take_profit)
>>>>>>> Stashed changes

        random_delay(page, 400, 1000)

        # 5. Fill in stop loss (robust toggle + fill)
        if stop_loss:
<<<<<<< Updated upstream
            # Locate the exact text element for Stop loss
            sl_label = page.locator('div:text-is("Stop loss"), div:text-is("Stop Loss")').first
            
            if sl_label.is_visible():
                # Go up one level to the parent container
                sl_parent = sl_label.locator('..')
                
                # Check if the checkmark SVG is currently visible inside this container
                is_checked = sl_parent.locator('svg#ic_checkmark, svg[id*="checkmark"]').is_visible()
                
                if not is_checked:
                    print("Stop Loss is OFF. Clicking to enable...")
                    sl_parent.click()
                    random_delay(page, 500, 1000)
                else:
                    print("Stop Loss is already ON. Skipping toggle.")

            # Now find the input box for SL and fill it
            sl_input = page.locator('input[placeholder="S/L"], .sl-input input, input[aria-label="Stop Loss"]').first
            if sl_input.is_visible():
                sl_input.click()
                page.keyboard.press("Control+A")
                page.keyboard.press("Backspace")
                sl_input.fill(str(stop_loss))
                page.keyboard.press("Enter")
                print(f"Entered stop loss: {stop_loss}")
=======
            print("Handling Stop Loss...")
            _ensure_field_enabled_and_fill(page, "Stop loss", "S/L", stop_loss)
>>>>>>> Stashed changes

        random_delay(page, 300, 800)
        print("Order input complete.")
        return True
        
    except Exception as e:
        print(f"Error during order input: {str(e)}")
        return False