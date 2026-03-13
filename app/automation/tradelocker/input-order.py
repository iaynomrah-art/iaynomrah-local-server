import random
from app.automation.tradelocker._ui import first_visible, clear_and_fill, get_text_if_visible


def random_delay(page, min_ms=700, max_ms=1800):
    delay = random.randint(min_ms, max_ms)
    page.wait_for_timeout(delay)


def _fill_first(page, selectors, value, field_name):
    target = first_visible(page, selectors, timeout=4000)
    if not target:
        return False

    clear_and_fill(target, page, value)
    print(f"Filled {field_name}: {value}")
    return True


def _select_instrument(page, symbol):
    symbol_text = str(symbol).strip().upper()
    # Prefer instrument list row on the right panel.
    for selector in [
        f'div[role="row"]:has-text("{symbol_text}")',
        f'tr:has-text("{symbol_text}")',
        f'div:has-text("{symbol_text}")',
    ]:
        try:
            row = page.locator(selector).first
            if row.is_visible(timeout=1200):
                row.click(timeout=1500)
                page.wait_for_timeout(220)
                return True
        except Exception:
            continue
    return False


def _ensure_side_selected(page, side):
    side_name = side.capitalize()
    side_btn = first_visible(page, [
        f'button:has-text("{side_name}")',
        f'div[role="button"]:has-text("{side_name}")',
        f'[data-testid*="{side}"]',
    ], timeout=3000)

    if not side_btn:
        return False

    try:
        side_btn.click(timeout=1500)
        return True
    except Exception:
        return False


def _set_amount(page, value):
    # Current TradeLocker panel commonly uses number/decimal input with +/- steppers.
    return _fill_first(page, [
        'input[name*="amount" i]',
        'input[name*="qty" i]',
        'input[name*="volume" i]',
        'input[inputmode="decimal"]',
        'input[type="number"]',
        'input[placeholder*="amount" i]',
        'input[placeholder*="quantity" i]',
        'input[placeholder*="lots" i]'
    ], value, "order amount")


def _toggle_and_fill(page, label_text, value):
    if not value:
        return False

    # Enable TP/SL control if it's checkbox/toggle based.
    toggle = first_visible(page, [
        f'label:has-text("{label_text}") input[type="checkbox"]',
        f'input[type="checkbox"][name*="{label_text}" i]',
        f'button:has-text("{label_text}")',
        f'div[role="checkbox"]:has-text("{label_text}")',
    ], timeout=1500)

    if toggle:
        try:
            checked = toggle.is_checked() if hasattr(toggle, "is_checked") else None
            if checked is False:
                toggle.click(timeout=1200)
        except Exception:
            try:
                toggle.click(timeout=1200)
            except Exception:
                pass

    return _fill_first(page, [
        f'input[name*="{label_text}" i]',
        f'input[placeholder*="{label_text}" i]',
        'input[name*="tp" i]' if label_text.lower().startswith("take") else 'input[name*="sl" i]',
        'input[placeholder*="tp" i]' if label_text.lower().startswith("take") else 'input[placeholder*="sl" i]',
    ], value, label_text.lower())


def input_order(page, purchase_type, order_amount, symbol, take_profit, stop_loss):
    try:
        if not symbol:
            return {"success": False, "reason": "symbol is required", "warning": None}
        if not order_amount:
            return {"success": False, "reason": "order_amount is required", "warning": None}
        if not purchase_type:
            return {"success": False, "reason": "purchase_type is required", "warning": None}

        random_delay(page, 300, 900)

        # Current TradeLocker flow: selecting the instrument row is the most reliable.
        selected = _select_instrument(page, symbol)

        symbol_open = first_visible(page, [
            'button[aria-label*="symbol" i]',
            '[data-testid*="symbol-selector"]',
            'div[role="combobox"]',
            'input[placeholder*="symbol" i]'
        ], timeout=1800)

        if symbol_open:
            try:
                symbol_open.click(timeout=1500)
            except Exception:
                pass

        symbol_input = first_visible(page, [
            'input[placeholder*="search" i]',
            'input[placeholder*="symbol" i]',
            'input[type="search"]'
        ], timeout=2500)

        if symbol_input and not selected:
            clear_and_fill(symbol_input, page, symbol)
            random_delay(page, 300, 700)
            pick = page.locator(f'text="{symbol}"').first
            if pick.is_visible(timeout=1500):
                pick.click(timeout=1500)
        elif not selected:
            page.keyboard.type(symbol)

        random_delay(page, 300, 700)

        side = purchase_type.lower().strip()
        if side not in ("buy", "sell"):
            return {"success": False, "reason": f"Invalid purchase_type: {purchase_type}", "warning": None}

        if not _ensure_side_selected(page, side):
            return {"success": False, "reason": f"Could not find {side} button", "warning": None}

        amount_ok = _set_amount(page, order_amount)

        if not amount_ok:
            # Last fallback: first visible text input after selecting side.
            fallback = page.locator('input[type="text"]').first
            if fallback.is_visible(timeout=1200):
                clear_and_fill(fallback, page, order_amount)
            else:
                return {"success": False, "reason": "Could not locate order amount input", "warning": None}

        if take_profit:
            _toggle_and_fill(page, "Take Profit", take_profit)

        if stop_loss:
            _toggle_and_fill(page, "Stop Loss", stop_loss)

        warning = None
        warning_el = page.locator(':text("market is closed"), :text("only pending"), :text("insufficient")').first
        warning = get_text_if_visible(warning_el, timeout=1200)

        return {"success": True, "reason": None, "warning": warning}

    except Exception as e:
        return {"success": False, "reason": str(e), "warning": None}
