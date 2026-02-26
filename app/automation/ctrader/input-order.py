import random
import re

def random_delay(page, min_ms=800, max_ms=2500):
    """Wait a random duration to appear more human-like."""
    delay = random.randint(min_ms, max_ms)
    page.wait_for_timeout(delay)

def _ensure_field_enabled_and_fill(page, label_text, value, timeout=5000):
    """Robustly locates the input by isolating the exact UI block."""
    label_locator = page.get_by_text(label_text, exact=True).first

    section_container = page.locator("div").filter(
        has=page.get_by_text(label_text, exact=True)
    ).filter(
        has=page.get_by_text("Pips", exact=True)
    ).filter(
        has_not_text="Quantity"
    ).filter(
        has_not_text="Place order"
    ).last
    
    input_locator = section_container.locator("input[type='text']").first

    try:
        input_locator.wait_for(state="visible", timeout=1000)
        input_locator.click(timeout=1000)
        page.keyboard.press("Control+A")
        page.keyboard.press("Backspace")
        input_locator.fill(str(value))
        print(f"  ✓ {label_text} field was already visible — filled Pips with {value}")
        return True
    except Exception:
        print(f"  ⏳ {label_text} field hidden — clicking text label to enable...")

    try:
        label_locator.wait_for(state="visible", timeout=timeout)
        label_locator.click()
        print(f"  ✓ Clicked '{label_text}' label")
    except Exception as e:
        print(f"  ✗ Could not find or click '{label_text}' label: {e}")
        return False

    random_delay(page, 400, 800)

    try:
        input_locator.wait_for(state="visible", timeout=timeout)
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
    """Fills in the order form fields using Geometric Layout Anchoring."""
    try:
        print(f"Inputting order: {purchase_type} {order_amount} {symbol} TP:{take_profit} SL:{stop_loss}")
        
        # --- 0. OBLITERATE THE ACCOUNT MENU ---
        print("Ensuring account menu and overlays are closed...")
        # Click the safe, blank app header bar at the top (X=500, Y=15) to forcefully remove focus from the menu
        page.mouse.click(500, 15)
        page.wait_for_timeout(300)
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)

        # --- 1. FIND THE GEOMETRIC ANCHOR (THE SELL BUTTON) ---
        try:
            anchor_btn = page.get_by_text(re.compile(r"^Sell\s*\d", re.IGNORECASE)).first
            anchor_btn.wait_for(state="visible", timeout=5000)
            anchor_box = anchor_btn.bounding_box()
            if not anchor_box:
                raise Exception("Anchor button has no physical dimensions.")
        except Exception as e:
            print("  ✗ Critical: Could not locate the New Order panel anchor (Sell button).")
            return False

        # --- 2. SEARCH AND SELECT THE SYMBOL ---
        try:
            print(f"Attempting to switch symbol to: {symbol}")
            dropdown_trigger = None
            dropdown_box = None
            
            # Instantly grab all dropdown elements on the page without waiting
            for el in page.locator('div[tabindex="1"]').all():
                if el.is_visible():
                    box = el.bounding_box()
                    # MATH: Is it physically ABOVE the Sell button, and inside the right-hand panel?
                    if box and box['y'] < anchor_box['y'] and abs(box['x'] - anchor_box['x']) < 250:
                        # Grab the one closest to the Sell button
                        if dropdown_box is None or box['y'] > dropdown_box['y']:
                            dropdown_trigger = el
                            dropdown_box = box
            
            if dropdown_trigger:
                dropdown_trigger.click(force=True)
                print("  ✓ Opened symbol dropdown menu via Geometric Layout")
            else:
                print("  ⏳ Geometric logic missed. Using Visual Fallback (DoM tab offset)...")
                # Fallback: Find the "DoM" tab and click 40 pixels directly beneath it
                dom_tab = page.get_by_text("DoM", exact=True).first
                db = dom_tab.bounding_box()
                page.mouse.click(db['x'] + 10, db['y'] + 40)
                print("  ✓ Clicked dropdown area using Visual Fallback")

            random_delay(page, 500, 1000)

            # Blind type the symbol into the auto-focused search box
            page.keyboard.type(symbol, delay=150)
            print(f"  ✓ Typed '{symbol}' into search")
            
            random_delay(page, 1000, 1500)

            # Select the exact text match from the dropdown list
            search_result = page.get_by_text(symbol, exact=True).last
            search_result.wait_for(state="visible", timeout=5000)
            search_result.click(force=True)
            print(f"  ✓ Successfully clicked and selected: {symbol}")
            
        except Exception as e:
            print(f"  ✗ Failed to change symbol to {symbol}. Error: {e}")
            return False 
            
        # Give React time to re-render the Buy/Sell prices for the new symbol
        random_delay(page, 1000, 1500)

        # --- 3. SELECT BUY OR SELL ---
        try:
            target_action = purchase_type.lower()
            if target_action == "buy":
                buy_btn = page.get_by_text(re.compile(r"^Buy\s*\d", re.IGNORECASE)).first
                buy_btn.wait_for(state="visible", timeout=5000)
                buy_btn.click()
                print("  ✓ Selected direction: Buy")
            elif target_action == "sell":
                sell_btn = page.get_by_text(re.compile(r"^Sell\s*\d", re.IGNORECASE)).first
                sell_btn.wait_for(state="visible", timeout=5000)
                sell_btn.click()
                print("  ✓ Selected direction: Sell")
            else:
                print(f"  ✗ Invalid purchase_type provided: {purchase_type}")
                return False
        except Exception as e:
            print(f"  ✗ Failed to select {purchase_type} direction. Error: {e}")
            return False

        random_delay(page, 400, 1000)

        # --- 4. FILL IN THE ORDER AMOUNT ---
        try:
            amount_input = page.locator('input[type="text"]').nth(1)
            quantity_input = page.locator('div:has-text("Quantity") + div input, .quantity-input input').first
            if quantity_input.is_visible():
                amount_input = quantity_input

            if amount_input.is_visible():
                amount_input.click()
                page.keyboard.press("Control+A")
                page.keyboard.press("Backspace")
                amount_input.fill(str(order_amount))
                print(f"  ✓ Entered order amount: {order_amount}")
        except Exception as e:
            print(f"  ✗ Failed to enter quantity: {e}")

        random_delay(page, 400, 1000)

        # --- 5. FILL IN TAKE PROFIT & STOP LOSS ---
        if take_profit:
            print("Handling Take Profit...")
            _ensure_field_enabled_and_fill(page, "Take profit", take_profit)

        random_delay(page, 400, 1000)

        if stop_loss:
            print("Handling Stop Loss...")
            _ensure_field_enabled_and_fill(page, "Stop loss", stop_loss)

        random_delay(page, 500, 1000)
        
        # --- 6. CLICK PLACE ORDER ---
        try:
            place_order_btn = page.get_by_text("Place order", exact=True).last
            place_order_btn.wait_for(state="visible", timeout=3000)
            place_order_btn.click(force=True)
            print("  ✓ Clicked 'Place order' button")
        except Exception as e:
            print(f"  ✗ Failed to click Place order button: {e}")
            return False

        print("Order input sequence complete.")
        return True
        
    except Exception as e:
        print(f"Critical error during order input: {str(e)}")
        return False