import random
import re

def random_delay(page, min_ms=800, max_ms=2500):
    """Wait a random duration to appear more human-like."""
    delay = random.randint(min_ms, max_ms)
    page.wait_for_timeout(delay)

def _find_nearest_input(page, label_box):
    """Find the visible text input closest to and just below the given label."""
    all_inputs = page.locator("input[type='text']").all()
    best_input = None
    best_distance = float('inf')

    for inp in all_inputs:
        try:
            if not inp.is_visible():
                continue
            box = inp.bounding_box()
            if not box:
                continue
            # Input should be below (or same row as) the label, and horizontally close
            y_diff = box['y'] - label_box['y']
            x_diff = abs(box['x'] - label_box['x'])
            if 0 <= y_diff < 80 and x_diff < 300:
                distance = y_diff + x_diff
                if distance < best_distance:
                    best_distance = distance
                    best_input = inp
        except Exception:
            continue
    return best_input


def _ensure_field_enabled_and_fill(page, label_text, value, timeout=5000):
    """Locates the input using geometric proximity to the label text."""
    label_locator = page.get_by_text(label_text, exact=True).first

    def _try_fill(inp):
        inp.click(timeout=1000)
        page.keyboard.press("Control+A")
        page.keyboard.press("Backspace")
        inp.fill(str(value))

    # --- Attempt 1: Field is already visible ---
    try:
        label_locator.wait_for(state="visible", timeout=2000)
        label_box = label_locator.bounding_box()
        if label_box:
            inp = _find_nearest_input(page, label_box)
            if inp:
                _try_fill(inp)
                print(f"  ✓ {label_text} field was already visible — filled Pips with {value}")
                return True
    except Exception:
        pass

    # --- Attempt 2: Click label to expand/enable, then find input ---
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
        label_box = label_locator.bounding_box()
        if label_box:
            inp = _find_nearest_input(page, label_box)
            if inp:
                _try_fill(inp)
                print(f"  ✓ {label_text} field appeared after toggle — filled Pips with {value}")
                return True
        print(f"  ✗ {label_text} input not found near label after toggle")
        return False
    except Exception as e:
        print(f"  ✗ {label_text} input did not become visible after toggle: {e}")
        return False

def input_order(page, purchase_type, order_amount, symbol, take_profit, stop_loss):
    """Fills in the order form fields using Geometric Layout Anchoring."""
    try:
        print(f"Inputting order: {purchase_type} {order_amount} {symbol} TP:{take_profit} SL:{stop_loss}")
        
        # --- 0. OBLITERATE THE ACCOUNT MENU ---
        print("Ensuring account menu and overlays are closed...")
        # Click the safe, blank app header bar at the top (X=500, Y=15)
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
                        if dropdown_box is None or box['y'] > dropdown_box['y']:
                            dropdown_trigger = el
                            dropdown_box = box
            
            if dropdown_trigger:
                dropdown_trigger.click(force=True)
                print("  ✓ Opened symbol dropdown menu via Geometric Layout")
            else:
                print("  ⏳ Geometric logic missed. Using Visual Fallback (DoM tab offset)...")
                dom_tab = page.get_by_text("DoM", exact=True).first
                db = dom_tab.bounding_box()
                page.mouse.click(db['x'] + 10, db['y'] + 40)
                print("  ✓ Clicked dropdown area using Visual Fallback")

            random_delay(page, 500, 1000)

            # --- NEW FIX: Clear the existing text before typing ---
            page.keyboard.press("Control+A")
            page.keyboard.press("Backspace")
            page.wait_for_timeout(200)

            # Blind type the symbol into the cleared, auto-focused search box
            page.keyboard.type(symbol, delay=150)
            print(f"  ✓ Cleared input and typed '{symbol}' into search")
            
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
        
        # --- 6. CHECK FOR WARNINGS (DO NOT CLICK) ---
        warning_text = None
        try:
            # Look specifically for the red warning banner below the Place Order button
            warning_el = page.locator(':text("The market is closed"), :text("Only pending orders are accepted"), :text("not available for trading"), :text("Insufficient funds")').first
            if warning_el.is_visible(timeout=1500):
                warning_text = warning_el.inner_text().strip()
                print(f"  ⚠ Warning detected: {warning_text}")
        except Exception:
            pass  # No warning found, proceed normally

        print("Order input sequence complete.")
        return {"success": True, "reason": None, "warning": warning_text}
        
    except Exception as e:
        print(f"Critical error during order input: {str(e)}")
        return {"success": False, "reason": str(e), "warning": None}
