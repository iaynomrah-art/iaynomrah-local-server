import importlib
import random
from app.automation.tradelocker._ui import first_visible, get_text_if_visible

input_order_module = importlib.import_module("app.automation.tradelocker.input-order")
input_order = input_order_module.input_order


def random_delay(page, min_ms=500, max_ms=1500):
    delay = random.randint(min_ms, max_ms)
    page.wait_for_timeout(delay)


def place_order(page):
    try:
        warning_el = page.locator(':text("market is closed"), :text("only pending"), :text("insufficient")').first
        warning_text = get_text_if_visible(warning_el, timeout=1200)

        candidates = [
            # Current TradeLocker submit style: BUY/SELL <amount> @ <price>
            'button:has-text("@")',
            'button:has-text("BUY"):has-text("@")',
            'button:has-text("SELL"):has-text("@")',
            'button:has-text("Place order")',
            'button:has-text("Place Order")',
            'button:has-text("Submit")',
            'button:has-text("Execute")',
            'button[type="submit"]',
            '[data-testid*="place-order"]',
            '[data-testid*="submit-order"]'
        ]

        execute_button = first_visible(page, candidates, timeout=1000)

        if not execute_button:
            return {"success": False, "reason": "Could not find TradeLocker place/submit order action", "warning": warning_text}

        is_disabled = False
        try:
            is_disabled = execute_button.is_disabled()
        except Exception:
            pass

        try:
            aria_disabled = execute_button.get_attribute("aria-disabled")
            if aria_disabled == "true":
                is_disabled = True
        except Exception:
            pass

        if warning_text and "closed" in warning_text.lower():
            is_disabled = True

        if is_disabled:
            return {"success": False, "reason": warning_text or "Place order button is disabled", "warning": warning_text}

        execute_button.click(timeout=5000)
        random_delay(page, 600, 1400)

        return {"success": True, "reason": None, "warning": warning_text}

    except Exception as e:
        return {"success": False, "reason": str(e), "warning": None}


def full_place_order(page, purchase_type, order_amount, symbol, take_profit, stop_loss):
    fill_result = input_order(page, purchase_type, order_amount, symbol, take_profit, stop_loss)
    if isinstance(fill_result, dict) and not fill_result.get("success", False):
        return fill_result
    if isinstance(fill_result, bool) and not fill_result:
        return {"success": False, "reason": "Failed to fill order details", "warning": None}

    random_delay(page, 300, 900)
    return place_order(page)
