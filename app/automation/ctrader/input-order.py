import random

def random_delay(page, min_ms=800, max_ms=2500):
    """Wait a random duration to appear more human-like."""
    delay = random.randint(min_ms, max_ms)
    page.wait_for_timeout(delay)


def _ensure_field_enabled_and_fill(page, label_text, value, timeout=5000):
    """
    Robustly locates the input by isolating the exact UI block.
    Uses negative filters to prevent Playwright from accidentally matching the entire form.
    """
    # 1. Target the literal text label for clicking (e.g., "Take profit")
    label_locator = page.get_by_text(label_text, exact=True).first

    # 2. Strict Container Locator:
    # - Must contain the label ("Take profit")
    # - Must contain the exact text "Pips" (proves it is expanded)
    # - MUST NOT contain "Quantity" or "Place order" (prevents bubbling up to the main form)
    section_container = page.locator("div").filter(
        has=page.get_by_text(label_text, exact=True)
    ).filter(
        has=page.get_by_text("Pips", exact=True)
    ).filter(
        has_not_text="Quantity"
    ).filter(
        has_not_text="Place order"
    ).last
    
    # The Pips input is always the first text input inside this specific isolated wrapper
    input_locator = section_container.locator("input[type='text']").first

    # --- Attempt 1: Check if input is already visible and expanded ---
    try:
        # Short wait to see if the isolated block resolves
        input_locator.wait_for(state="visible", timeout=1000)
        
        # If found, click it explicitly to move focus
        input_locator.click(timeout=1000)
        page.keyboard.press("Control+A")
        page.keyboard.press("Backspace")
        input_locator.fill(str(value))
        
        print(f"  ✓ {label_text} field was already visible — filled Pips with {value}")
        return True
    except Exception:
        print(f"  ⏳ {label_text} field hidden — clicking text label to enable...")

    # --- Attempt 2: Click the label text to toggle the field on ---
    try:
        label_locator.wait_for(state="visible", timeout=timeout)
        label_locator.click()
        print(f"  ✓ Clicked '{label_text}' label")
    except Exception as e:
        print(f"  ✗ Could not find or click '{label_text}' label: {e}")
        return False

    # Brief human-like pause while the DOM renders the new input fields
    random_delay(page, 400, 800)

    # --- Attempt 3: Wait explicitly for the input to mount in the DOM ---
    try:
        # Now that it's expanded, the section_container will successfully resolve
        input_locator.wait_for(state="visible", timeout=timeout)
        
        # Explicit click ensures focus is on THIS input
        input_locator.click(timeout=1000)
        page.keyboard.press("Control+A")
        page.keyboard.press("Backspace")
        input_locator.fill(str(value))
        
        print(f"  ✓ {label_text} field appeared after toggle — filled Pips with {value}")
        return True
    except Exception as e:
        print(f"  ✗ {label_text} input did not become visible after toggle: {e}")
        return False


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
        amount_input = page.locator('input[type="text"]').nth(1)
        quantity_input = page.locator('div:has-text("Quantity") + div input, .quantity-input input').first
        if quantity_input.is_visible():
            amount_input = quantity_input

        if amount_input.is_visible():
            amount_input.click()
            page.keyboard.press("Control+A")
            page.keyboard.press("Backspace")
            amount_input.fill(str(order_amount))
            print(f"Entered order amount: {order_amount}")

        random_delay(page, 400, 1000)

        # 4. Fill in take profit
        if take_profit:
            print("Handling Take Profit...")
            _ensure_field_enabled_and_fill(page, "Take profit", take_profit)

        random_delay(page, 400, 1000)

        # 5. Fill in stop loss
        if stop_loss:
            print("Handling Stop Loss...")
            _ensure_field_enabled_and_fill(page, "Stop loss", stop_loss)

        random_delay(page, 300, 800)
        print("Order input complete.")
        return True
    except Exception as e:
        print(f"Error during order input: {str(e)}")
        return False