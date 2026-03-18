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


def _find_price_row_input(page, tp_sl_label_box):
    """
    For the TP/SL section, explicitly find the input on the row labeled 'Price'
    within the same column as the TP/SL label.
    """
    try:
        label_center_x = tp_sl_label_box["x"] + (tp_sl_label_box.get("width") or 0) / 2
    except Exception:
        return None

    best_price_label_box = None
    best_score = float("inf")

    for el in page.get_by_text("Price", exact=True).all():
        try:
            if not el.is_visible():
                continue
            box = el.bounding_box()
            if not box:
                continue

            el_center_x = box["x"] + (box.get("width") or 0) / 2
            x_diff = abs(el_center_x - label_center_x)
            y_diff = box["y"] - tp_sl_label_box["y"]

            # Price row label should be below the TP/SL label and in the same column.
            if 0 <= y_diff < 260 and x_diff < 180:
                score = y_diff + x_diff
                if score < best_score:
                    best_score = score
                    best_price_label_box = box
        except Exception:
            continue

    if not best_price_label_box:
        return None

    # Find the input on the same horizontal row as the 'Price' label, and to its left.
    price_center_y = best_price_label_box["y"] + (best_price_label_box.get("height") or 0) / 2
    inputs = page.locator("input[type='text']").all()

    best_inp = None
    best_inp_score = float("inf")

    for inp in inputs:
        try:
            if not inp.is_visible():
                continue
            ibox = inp.bounding_box()
            if not ibox:
                continue

            inp_center_x = ibox["x"] + (ibox.get("width") or 0) / 2
            inp_center_y = ibox["y"] + (ibox.get("height") or 0) / 2

            # Same row as "Price"
            y_same_row = abs(inp_center_y - price_center_y)
            if y_same_row > 26:
                continue

            # Input is left of the "Price" label text
            if ibox["x"] >= best_price_label_box["x"]:
                continue

            # Keep it within the same TP/SL column
            if abs(inp_center_x - label_center_x) > 220:
                continue

            score = y_same_row + abs(inp_center_x - label_center_x) * 0.2
            if score < best_inp_score:
                best_inp_score = score
                best_inp = inp
        except Exception:
            continue

    return best_inp


def _find_price_input(page, label_box):
    """Find the Price-row input nearest to a TP/SL label region."""
    all_inputs = page.locator("input[type='text']").all()
    candidates = []

    label_center_x = label_box["x"] + (label_box.get("width") or 0) / 2

    for inp in all_inputs:
        try:
            if not inp.is_visible():
                continue
            box = inp.bounding_box()
            if not box:
                continue

            y_diff = box['y'] - label_box['y']
            inp_center_x = box["x"] + (box.get("width") or 0) / 2
            x_diff = abs(inp_center_x - label_center_x)

            # Keep reasonably-close inputs; we'll further restrict by column below.
            if 0 <= y_diff < 180 and x_diff < 360:
                candidates.append((x_diff, box['y'], inp))
        except Exception:
            continue

    if not candidates:
        return None

    # First, lock to the closest "column" (X proximity). This prevents TP/SL swapping
    # when both columns fall within the broad proximity window.
    candidates.sort(key=lambda item: (item[0], item[1]))  # (x_diff, y, inp)
    best_x = candidates[0][0]
    same_column = [c for c in candidates if c[0] <= best_x + 40]
    same_column.sort(key=lambda item: item[1])  # by y only

    # Rows are typically ordered as: Pips, Price, %.
    if len(same_column) >= 2:
        return same_column[1][2]

    return same_column[0][2]


def _ensure_field_enabled_and_fill(page, label_text, value, timeout=5000):
    """Locates the input using geometric proximity to the label text."""
    label_locator = page.get_by_text(label_text, exact=True).first

    def _try_fill(inp):
        inp.click(timeout=1000)
        page.keyboard.press("Control+A")
        page.keyboard.press("Backspace")
        inp.fill(str(value))

    def _try_fill_via_click_target(click_target):
        click_target.click(timeout=1500)
        page.keyboard.press("Control+A")
        page.keyboard.press("Backspace")
        page.keyboard.type(str(value), delay=20)

    # --- Attempt 0: Use explicit codegen selectors for Profit inputs ---
    # These are more reliable than geometric proximity for the TP/SL panel.
    try:
        if label_text == "Stop loss":
            sl_profit_click = page.locator(
                "div:nth-child(5) > .root_x.root_eu.root_di.root_do.root_co > .root_gb.root_x > "
                ".root_di.root_x.root_ef.root_eg > .root_-4 > .root_di.root_do"
            ).first
            if sl_profit_click.is_visible(timeout=800):
                _try_fill_via_click_target(sl_profit_click)
                print(f"  ✓ {label_text} (Profit) filled via explicit locator with {value}")
                return True
        elif label_text == "Take profit":
            tp_profit_click = page.locator(
                "div:nth-child(3) > div:nth-child(5) > .root_x.root_eu.root_di.root_do.root_co > "
                ".root_gb.root_x > .root_di.root_x.root_ef.root_eg > .root_-4 > .root_di.root_do"
            ).first
            if tp_profit_click.is_visible(timeout=800):
                _try_fill_via_click_target(tp_profit_click)
                print(f"  ✓ {label_text} (Profit) filled via explicit locator with {value}")
                return True
    except Exception:
        # Fall back to geometric logic below
        pass

    # --- Attempt 1: Field is already visible ---
    try:
        label_locator.wait_for(state="visible", timeout=2000)
        label_box = label_locator.bounding_box()
        if label_box:
            # Prefer the explicit "Price" row input rather than the Pips row.
            inp = _find_price_row_input(page, label_box) or _find_price_input(page, label_box)
            if inp:
                _try_fill(inp)
                print(f"  ✓ {label_text} field was already visible — filled Price with {value}")
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
            # Prefer the explicit "Price" row input rather than the Pips row.
            inp = _find_price_row_input(page, label_box) or _find_price_input(page, label_box)
            if inp:
                _try_fill(inp)
                print(f"  ✓ {label_text} field appeared after toggle — filled Price with {value}")
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
        return {"success": True, "reason": None, "warning": None}
        
    except Exception as e:
        print(f"Critical error during order input: {str(e)}")
        return {"success": False, "reason": str(e), "warning": None}
