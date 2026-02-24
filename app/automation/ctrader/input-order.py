import random

def random_delay(page, min_ms=800, max_ms=2500):
    """Wait a random duration to appear more human-like."""
    delay = random.randint(min_ms, max_ms)
    page.wait_for_timeout(delay)

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
        # Attempt to find the quantity input reliably
        amount_input = page.locator('div:has-text("Quantity") + div input, .quantity-input input, input[aria-label="Volume"]').first
        if not amount_input.is_visible():
            amount_input = page.locator('input[type="text"]').nth(1) # Fallback

        if amount_input.is_visible():
            amount_input.click()
            page.keyboard.press("Control+A")
            page.keyboard.press("Backspace")
            amount_input.fill(str(order_amount))
            page.keyboard.press("Enter") # Lock in the value
            print(f"Entered order amount: {order_amount}")

        random_delay(page, 400, 1000)

        # 4. Fill in take profit
        if take_profit:
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

        random_delay(page, 400, 1000)

        # 5. Fill in stop loss
        if stop_loss:
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

        random_delay(page, 300, 800)
        print("Order input complete.")
        return True
        
    except Exception as e:
        print(f"Error during order input: {str(e)}")
        return False