import importlib
import random


# ---------------------------------------------------------------------------
# UI helpers (inlined – no _ui.py dependency)
# ---------------------------------------------------------------------------

def first_visible(page, selectors, timeout=3000):
    """Return the first visible locator from candidate selectors."""
    for selector in selectors:
        try:
            loc = page.locator(selector).first
            if loc.is_visible(timeout=timeout):
                return loc
        except Exception:
            continue
    return None


def get_text_if_visible(locator, timeout=1000):
    try:
        if locator.is_visible(timeout=timeout):
            return (locator.inner_text() or "").strip()
    except Exception:
        pass
    return None

input_order_module = importlib.import_module("app.automation.tradelocker.input-order")
input_order = input_order_module.input_order


def random_delay(page, min_ms=500, max_ms=1500):
    delay = random.randint(min_ms, max_ms)
    page.wait_for_timeout(delay)


def place_order(page):
    print("------- ENTERING place_order (submit) -------")
    try:
        warning_el = page.locator(':text("market is closed"), :text("only pending"), :text("insufficient")').first
        warning_text = get_text_if_visible(warning_el, timeout=1200)
        if warning_text:
            print(f"[submit-debug] Found warning text on page: {warning_text}")

        import re as _re

        # Primary: get_by_role with a non-anchored regex — handles multi-line button
        # text like "SELL 0.10\n@ 5102.40" where ^ anchor would fail.
        execute_button = None
        try:
            # Match "SELL 0.1 @" or "BUY 2.5 @" etc. (handles any spaces/newlines in between)
            btn_pattern = _re.compile(r"(SELL|BUY).+@", _re.I)
            print(f"[submit-debug] Trying Strategy 1: get_by_role Regex '{btn_pattern.pattern}'")
            btn = page.get_by_role("button", name=btn_pattern).first
            if btn.is_visible(timeout=3000):
                text = (btn.inner_text() or "").strip().replace('\n', ' ')
                print(f"[submit-debug] get_by_role matched: '{text}'")
                execute_button = btn
            else:
                print(f"[submit-debug] get_by_role found button but it is not visible")
        except Exception as e:
            print(f"[submit-debug] get_by_role failed: {e}")

        # Secondary: filter by has_text (excluding tab roles to avoid clicking Buy/Sell tabs)
        if not execute_button:
            try:
                print(f"[submit-debug] Trying Strategy 2: filter(has_text=...)")
                # We want a button that isn't a toggle tab, containing SELL/BUY + number.
                btn = page.locator('button:not([role="tab"])').filter(
                    has_text=_re.compile(r"(BUY|SELL)\s+[\d\.]+", _re.I)
                ).first
                if btn.is_visible(timeout=2000):
                    bb = btn.bounding_box()
                    text = (btn.inner_text() or "").strip().replace('\n', ' ')
                    print(f"[submit-debug] filter matched: text='{text}' bounds={bb}")
                    execute_button = btn
                else:
                    print(f"[submit-debug] filter found button but it is not visible")
            except Exception as e:
                print(f"[submit-debug] filter failed: {e}")

        if not execute_button:
            print(f"[submit-debug] Trying Strategy 3: Fallback specific candidates")
            candidates = [
                # Catch-all TradeLocker submit styles
                'button:has-text("@"):not([role="tab"])',
                'button.chakra-button[type="button"]:has-text("BUY"):not([role="tab"])',
                'button.chakra-button[type="button"]:has-text("SELL"):not([role="tab"])',
                'button:has-text("Place order")',
                'button:has-text("Submit")',
                '[data-testid*="place-order"]',
            ]
            execute_button = first_visible(page, candidates, timeout=1000)

        if not execute_button:
            print("[submit-debug] FATAL: Could not find TradeLocker place/submit order action")
            return {"success": False, "reason": "Could not find TradeLocker place/submit order action", "warning": warning_text}

        is_disabled = False
        try:
            is_disabled = execute_button.is_disabled()
            print(f"[submit-debug] Button builtin disabled state: {is_disabled}")
        except Exception as e:
            print(f"[submit-debug] Button is_disabled check failed: {e}")
            pass

        try:
            aria_disabled = execute_button.get_attribute("aria-disabled")
            if aria_disabled == "true":
                print("[submit-debug] Button is disabled via aria-disabled='true'")
                is_disabled = True
        except Exception:
            pass

        if warning_text and "closed" in warning_text.lower():
            print("[submit-debug] OVERRIDE: Forcing disabled state because warning text contains 'closed'")
            is_disabled = True

        if is_disabled:
            print(f"[submit-debug] ABORTING CLICK. Button is disabled. Reason/Warning: {warning_text}")
            return {"success": False, "reason": warning_text or "Place order button is disabled", "warning": warning_text}

        print("[submit-debug] CLICKING Execute Button now...")
        execute_button.click(timeout=5000, force=True)
        print("[submit-debug] Click successful. Waiting for random delay...")
        random_delay(page, 600, 1400)
        
        print("------- EXITING place_order (SUCCESS) -------")
        return {"success": True, "reason": None, "warning": warning_text}

    except Exception as e:
        print(f"[submit-debug] FATAL Error inside place_order: {str(e)}")
        return {"success": False, "reason": str(e), "warning": None}


def full_place_order(page, purchase_type, order_amount, symbol, take_profit, stop_loss):
    print("======= ENTERING full_place_order =======")
    fill_result = input_order(page, purchase_type, order_amount, symbol, take_profit, stop_loss)
    print(f"[full-order-debug] input_order result: {fill_result}")
    
    if isinstance(fill_result, dict) and not fill_result.get("success", False):
        print(f"[full-order-debug] Aborting because input_order failed/returned False: {fill_result}")
        return fill_result
    if isinstance(fill_result, bool) and not fill_result:
        print(f"[full-order-debug] Aborting because input_order returned boolean False")
        return {"success": False, "reason": "Failed to fill order details", "warning": None}

    print("[full-order-debug] Form filled. Initiating place_order execution...")
    random_delay(page, 300, 900)
    result = place_order(page)
    print(f"======= EXITING full_place_order (Result: {result}) =======")
    return result
