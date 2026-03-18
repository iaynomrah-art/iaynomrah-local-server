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


def clear_and_fill(locator, page, value):
    """Clear an input and fill with value."""
    try:
        locator.scroll_into_view_if_needed(timeout=2000)
    except Exception:
        pass
    locator.click(timeout=4000)
    page.keyboard.press("Control+A")
    page.keyboard.press("Backspace")
    locator.fill(str(value))


def get_text_if_visible(locator, timeout=1000):
    try:
        if locator.is_visible(timeout=timeout):
            return (locator.inner_text() or "").strip()
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def random_delay(page, min_ms=700, max_ms=1800):
    delay = random.randint(min_ms, max_ms)
    page.wait_for_timeout(delay)


def _click_instrument_expandable(page):
    """
    Click the expand chevron at the far-right of the mini order panel header.
    Codegen-recorded selector: page.locator('.chakra-button.css-qbgzru').click()
    """

    # Strategy 1: Exact codegen selector (highest priority).
    try:
        btn = page.locator(".chakra-button.css-qbgzru").first
        if btn.is_visible(timeout=3000):
            print("[expand] Codegen selector hit: .chakra-button.css-qbgzru")
            btn.click(timeout=2000)
            page.wait_for_timeout(500)
            return True
    except Exception as e:
        print(f"[expand] Codegen selector failed: {e}")

    # Strategy 2: aria / testid / title attributes.
    for sel in [
        'button[aria-label*="expand" i]',
        'button[title*="expand" i]',
        '[data-testid*="expand" i]',
        'button[aria-label*="full" i]',
        'button[title*="full" i]',
    ]:
        try:
            btn = page.locator(sel).first
            if btn.is_visible(timeout=600):
                label = btn.get_attribute("aria-label") or ""
                print(f"[expand] aria/title selector hit: sel='{sel}' label='{label}'")
                btn.click(timeout=1000)
                page.wait_for_timeout(500)
                return True
        except Exception:
            continue

    # Strategy 2: Codegen-style — button containing an SVG icon whose class
    # includes "expand", "maximize", "fullscreen", or "arrow" (TradeLocker uses
    # icon font / inline SVG with class names like 'icon-expand-arrows').
    for icon_cls in [
        "expand", "maximize", "fullscreen", "arrow-up-right",
        "enlarge", "open", "external", "arrows",
    ]:
        try:
            # Matches: <button><svg class="...expand..."/></button>
            btn = page.locator(f"button:has(svg[class*='{icon_cls}' i])").first
            if btn.is_visible(timeout=600):
                print(f"[expand] SVG icon class hit: '{icon_cls}'")
                btn.click(timeout=1000)
                page.wait_for_timeout(500)
                return True
        except Exception:
            continue

        try:
            # Matches: <button><i class="icon-expand"/></button>  (icon fonts)
            btn = page.locator(f"button:has(i[class*='{icon_cls}' i])").first
            if btn.is_visible(timeout=600):
                print(f"[expand] <i> icon class hit: '{icon_cls}'")
                btn.click(timeout=1000)
                page.wait_for_timeout(500)
                return True
        except Exception:
            continue

    # Strategy 3: Codegen-style DOM traversal — find the MARKET/LIMIT button,
    # get its PARENT container element, then pick the LAST button child of that
    # container. This avoids page-wide coordinate math entirely.
    try:
        market_btn = page.locator(
            'button:has-text("MARKET"), button:has-text("LIMIT")'
        ).first
        if not market_btn.is_visible(timeout=3000):
            raise Exception("MARKET button not visible")

        # Go up to the immediate parent, then find all direct button children.
        # Playwright's locator chaining: parent via xpath "/.."
        parent = market_btn.locator("xpath=..")
        sibling_btns = parent.locator("button").all()

        visible_btns = []
        for b in sibling_btns:
            try:
                if b.is_visible(timeout=300):
                    txt = ""
                    try:
                        txt = b.inner_text()[:30].strip()
                    except Exception:
                        pass
                    lbl = b.get_attribute("aria-label") or ""
                    print(f"[expand] Sibling button: text='{txt}' aria-label='{lbl}'")
                    visible_btns.append(b)
            except Exception:
                continue

        if not visible_btns:
            # Try one level higher
            grandparent = market_btn.locator("xpath=../..")
            sibling_btns = grandparent.locator("button").all()
            for b in sibling_btns:
                try:
                    if b.is_visible(timeout=300):
                        visible_btns.append(b)
                except Exception:
                    continue

        if visible_btns:
            # The expand button is the last sibling — not the MARKET button itself.
            # Filter out the MARKET/LIMIT button by checking inner text.
            non_market = [
                b for b in visible_btns
                if (b.inner_text() or "").strip().upper() not in ("MARKET", "LIMIT")
            ]
            target = non_market[-1] if non_market else visible_btns[-1]
            lbl = target.get_attribute("aria-label") or ""
            print(f"[expand] Clicking last sibling button: aria-label='{lbl}'")
            target.click(timeout=1500)
            page.wait_for_timeout(500)
            return True

    except Exception as e:
        print(f"[expand] Strategy 3 (DOM sibling) failed: {e}")

    print("[expand] WARNING: Could not click expand button. Order form may already be open.")
    return False


def _click_instrument_selector(page, symbol_text):
    """
    In the expanded order form, click the instrument selector button at the top
    (shows the current instrument's currency flag + name). Playwright codegen
    records this as getByRole('button', { name: 'Currency flag {SYMBOL} Currency'}).
    Clicking it opens the instrument search modal.
    """
    import re as _re

    # STRATEGY 1: Exact Codegen Regex pattern for the "Currency flag...Currency" accessible name.
    # We iterate over all matches and pick the one that is on the right side of the screen
    # (to avoid the left-side watchlist).
    try:
        candidates = page.get_by_role(
            "button",
            name=_re.compile(r"currency flag .+ currency", _re.I)
        ).all()
        
        for btn in candidates:
            if btn.is_visible(timeout=500):
                bb = btn.bounding_box()
                if bb:
                    # The main order panel is almost always on the right half of the screen
                    viewport = page.viewport_size
                    if viewport and bb["x"] > (viewport["width"] * 0.4):
                        print(f"[instrument-selector] Found valid main panel button via Regex: bounds={bb}")
                        btn.click(timeout=3000, force=True)
                        page.wait_for_timeout(600)
                        return True
    except Exception as e:
        print(f"[instrument-selector] Strategy 1 (Regex) failed: {e}")

    # STRATEGY 2: Structural DOM navigation.
    # The instrument selector is always sitting above the MARKET/LIMIT row in the order panel.
    try:
        market_btn = page.locator('button:has-text("MARKET"), button:has-text("LIMIT")').first
        if market_btn.is_visible(timeout=2000):
            # Go up 4-5 levels to the main order card container
            card = market_btn.locator("xpath=../../../..")
            
            # Inside this card, find a button that looks like a currency selector.
            # Usually contains an SVG/img flag, or has a specific data-testid.
            selector_btn = first_visible(card, [
                'button[aria-label*="currency flag" i]',
                'button:has([class*="flag" i])',
                'button:has([data-testid*="flag" i])',
                'button:has([class*="currency" i])',
            ], timeout=1000)
            
            if selector_btn:
                bb = selector_btn.bounding_box()
                print(f"[instrument-selector] Found via Structural DOM (inside order card): bounds={bb}")
                selector_btn.click(timeout=3000, force=True)
                page.wait_for_timeout(600)
                return True
    except Exception as e:
        print(f"[instrument-selector] Strategy 2 (Structural) failed: {e}")

    # STRATEGY 3: Fallback loose selectors on the whole page, prioritizing the right side.
    fallback = [
        'button[aria-label*="currency flag" i]',
        '[data-panel-id] button:has([class*="flag" i])',
        'button:has(img[alt*="flag" i])'
    ]
    for sel in fallback:
        try:
            elements = page.locator(sel).all()
            for el in elements:
                if el.is_visible(timeout=500):
                    bb = el.bounding_box()
                    viewport = page.viewport_size
                    if bb and viewport and bb["x"] > (viewport["width"] * 0.4):
                        print(f"[instrument-selector] Fallback hit: sel='{sel}' bounds={bb}")
                        el.click(timeout=2000, force=True)
                        page.wait_for_timeout(600)
                        return True
        except Exception:
            continue

    print(f"[instrument-selector] WARNING: Not found. Proceeding anyway.")
    return False


def _search_and_select_symbol(page, symbol_text):
    """
    After the instrument search modal opens, type the symbol and click the result.
    Only types into a search/modal input — NOT the global instruments search bar.
    """
    # Wait briefly for a modal-style search input to appear after clicking selector.
    search_input = first_visible(page, [
        '[role="dialog"] input',
        '[role="listbox"] input',
        'input[type="search"]',
        'input[placeholder*="search" i]',
        'input[placeholder*="symbol" i]',
        'input[placeholder*="instrument" i]',
        '[role="searchbox"]',
    ], timeout=3000)

    if search_input:
        bb = search_input.bounding_box()
        placeholder = search_input.get_attribute("placeholder") or ""
        print(f"[search] Typing '{symbol_text}' into: placeholder='{placeholder}' bounds={bb}")
        
        # FIX: The search input click is being intercepted by panels/sticky headers.
        # Use force=True to bypass Playwright's actionability checks, or just fill directly.
        try:
            search_input.click(timeout=2000, force=True)
            page.keyboard.press("Control+A")
            page.keyboard.press("Backspace")
            search_input.fill(symbol_text, force=True)
        except Exception as e:
            print(f"[search] Force click/fill failed: {e}. Trying direct fill.")
            try:
                search_input.fill(symbol_text, force=True)
            except Exception as e2:
                print(f"[search] Direct fill also failed: {e2}")

        # Explicitly wait up to 5 seconds for the search results to populate
        page.wait_for_timeout(5000)
    else:
        print(f"[search] WARNING: No search input found after instrument selector click.")

    # Click the matching result row.
    result_selectors = [
        f'button[name*="Currency Flag {symbol_text}"]',
        f'button[aria-label*="{symbol_text}"]',
        f'[role="option"]:has-text("{symbol_text}")',
        f'[role="row"]:has-text("{symbol_text}")',
        f'li:has-text("{symbol_text}")',
        f'div[class*="option"]:has-text("{symbol_text}")',
    ]

    for selector in result_selectors:
        try:
            result = page.locator(selector).first
            if result.is_visible(timeout=5000):
                rbb = result.bounding_box()
                print(f"[search] Result hit: sel='{selector}' bounds={rbb}")
                # Force click on result too, in case sticky headers intercept
                result.click(timeout=2000, force=True)
                page.wait_for_timeout(400)
                print(f"[search] Selected instrument: {symbol_text}")
                return True
        except Exception:
            continue

    # Last resort: press Enter.
    try:
        page.keyboard.press("Enter")
        page.wait_for_timeout(300)
        print(f"[search] Pressed Enter as last resort.")
        return True
    except Exception:
        pass

    print(f"[search] WARNING: Could not find result for '{symbol_text}'.")
    return False




def _ensure_side_selected(page, side):
    """
    Click the Buy or Sell tab in the order form.
    Codegen revealed these are <div> elements with exact text 'Buy' / 'Sell',
    matched via: locator('div').filter(hasText: /^Buy$/)
    """
    import re as _re
    side_name = side.capitalize()  # "Buy" or "Sell"

    # Primary: exact-text div filter (from codegen).
    try:
        btn = page.locator("div").filter(has_text=_re.compile(rf"^{side_name}$")).first
        if btn.is_visible(timeout=4000):
            bb = btn.bounding_box()
            print(f"[side] Clicking '{side_name}' div: bounds={bb}")
            btn.click(timeout=2000)
            page.wait_for_timeout(300)
            return True
    except Exception as e:
        print(f"[side] div filter failed: {e}")

    # Fallbacks.
    fallbacks = [
        f'div:text-is("{side_name}")',
        f'[role="tab"]:text-is("{side_name}")',
        f'button:has-text("{side_name}")',
        f'div[role="button"]:has-text("{side_name}")',
        f'[data-testid*="{side.lower()}"]',
        f'[aria-label*="{side_name}" i]',
    ]
    for sel in fallbacks:
        try:
            el = page.locator(sel).first
            if el.is_visible(timeout=1000):
                bb = el.bounding_box()
                print(f"[side] Fallback hit: sel='{sel}' bounds={bb}")
                el.click(timeout=2000)
                page.wait_for_timeout(300)
                return True
        except Exception:
            continue

    print(f"[side] WARNING: Could not find '{side_name}' button.")
    return False


def _fill_first(page, selectors, value, field_name):
    target = first_visible(page, selectors, timeout=4000)
    if not target:
        return False
    clear_and_fill(target, page, value)
    print(f"Filled {field_name}: {value}")
    return True


def _set_amount(page, value):
    """
    Set the order amount.
    Codegen pattern: getByRole('textbox', { name: 'lots' })
    """
    import re as _re
    try:
        # Codegen exact match pattern
        target = page.get_by_role("textbox", name=_re.compile(r"lots", _re.I)).first
        if target.is_visible(timeout=3000):
            print(f"[amount] Found via get_by_role('textbox', name='lots')")
            clear_and_fill(target, page, value)
            print(f"Filled order amount: {value}")
            return True
    except Exception as e:
        print(f"[amount] get_by_role failed: {e}")

    # Fallback to general selectors
    return _fill_first(page, [
        'input[name*="amount" i]',
        'input[name*="qty" i]',
        'input[name*="volume" i]',
        'input[inputmode="decimal"]',
        'input[type="number"]',
        'input[placeholder*="amount" i]',
        'input[placeholder*="quantity" i]',
        'input[placeholder*="lots" i]',
    ], value, "order amount")


def _toggle_and_fill(page, label_text, value):
    """
    Turn on TP/SL if needed, then fill the P&L input (preferred).
    """
    if not value:
        return False

    import re as _re
    
    # 1. Click the toggle label if not already checked
    try:
        label_loc = page.locator("label").filter(has_text=_re.compile(rf"^{label_text}$")).first
        if label_loc.is_visible(timeout=2000):
            print(f"[{label_text}] Found toggle label via codegen filter")
            
            checkbox = label_loc.locator('input[type="checkbox"]').first
            is_checked = False
            try:
                if checkbox.is_visible(timeout=500):
                    is_checked = checkbox.is_checked()
            except Exception:
                pass
                
            if not is_checked:
                print(f"[{label_text}] Toggle is OFF, clicking to enable...")
                label_loc.click(timeout=1500)
                page.wait_for_timeout(400)
            else:
                print(f"[{label_text}] Toggle is already ON.")
                
        else:
            toggle = first_visible(page, [
                f'button:has-text("{label_text}")',
                f'div[role="checkbox"]:has-text("{label_text}")',
            ], timeout=1000)
            if toggle:
                toggle.click(timeout=1200)
                page.wait_for_timeout(400)
    except Exception as e:
        print(f"[{label_text}] Toggle logic failed: {e}")

    # 2. Fill the specific input field (prefer P&L, fallback to price)
    
    # TRY BLOCK 1: Regex Match
    try:
        # FIX: Removed the unescaped forward slash (p/l) from the regex to prevent 
        # Playwright's JS engine from treating it as an early terminator.
        pnl_name_rx = _re.compile(
            rf"{_re.escape(label_text)}\s*(p&l|pl|pnl)\b",
            _re.I,
        )
        target = page.get_by_role("textbox", name=pnl_name_rx).first
        if target.is_visible(timeout=1200):
            print(f"[{label_text}] Found input via get_by_role('textbox', name=/{pnl_name_rx.pattern}/i)")
            clear_and_fill(target, page, value)
            print(f"Filled {label_text.lower()} (p&l): {value}")
            return True
    except Exception as e:
        print(f"[{label_text}] Regex input get_by_role failed: {e}")

    # TRY BLOCK 2: Exact Match Fallbacks
    # Separated so it doesn't get skipped if the regex above fails
    try:
        preferred_names = [f"{label_text} P&L", f"{label_text} P/L", f"{label_text} PL", f"{label_text} PNL"]
        for input_name in preferred_names:
            target = page.get_by_role("textbox", name=_re.compile(rf"^{_re.escape(input_name)}$", _re.I)).first
            if target.is_visible(timeout=800):
                print(f"[{label_text}] Found input via get_by_role('textbox', name='{input_name}')")
                clear_and_fill(target, page, value)
                print(f"Filled {label_text.lower()} (p&l): {value}")
                return True

        # Backward-compatible fallback: older UI used a price textbox
        legacy_input_name = f"{label_text} price"
        target = page.get_by_role("textbox", name=_re.compile(rf"{legacy_input_name}", _re.I)).first
        if target.is_visible(timeout=1200):
            print(f"[{label_text}] Found legacy input via get_by_role('textbox', name='{legacy_input_name}')")
            clear_and_fill(target, page, value)
            print(f"Filled {label_text.lower()} (price): {value}")
            return True
    except Exception as e:
        print(f"[{label_text}] Exact/Legacy input get_by_role failed: {e}")

    # 3. Last Resort Fallback
    return _fill_first(page, [
        f'input[aria-label*="{label_text}" i][aria-label*="p&l" i]',
        f'input[placeholder*="{label_text}" i][placeholder*="p&l" i]',
        f'input[name*="{label_text}" i]',
        f'input[placeholder*="{label_text}" i]',
        'input[name*="tp" i]' if label_text.lower().startswith("take") else 'input[name*="sl" i]',
        'input[placeholder*="tp" i]' if label_text.lower().startswith("take") else 'input[placeholder*="sl" i]',
    ], value, label_text.lower())


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def input_order(page, purchase_type, order_amount, symbol, take_profit, stop_loss):
    try:
        if not symbol:
            return {"success": False, "reason": "symbol is required", "warning": None}
        if not order_amount:
            return {"success": False, "reason": "order_amount is required", "warning": None}
        if not purchase_type:
            return {"success": False, "reason": "purchase_type is required", "warning": None}

        symbol_text = str(symbol).strip().upper()
        side = purchase_type.lower().strip()
        if side not in ("buy", "sell"):
            return {"success": False, "reason": f"Invalid purchase_type: {purchase_type}", "warning": None}

        random_delay(page, 300, 700)

        # ── Step 1: Click the expand icon in the instruments panel to open the order form.
        _click_instrument_expandable(page)
        random_delay(page, 300, 600)

        # ── Step 2: Click the instrument selector button at the top of the order form.
        _click_instrument_selector(page, symbol_text)
        random_delay(page, 300, 600)

        # ── Step 3: Search for and select the target symbol.
        _search_and_select_symbol(page, symbol_text)
        random_delay(page, 400, 800)

        # ── Step 4: Click Buy or Sell.
        if not _ensure_side_selected(page, side):
            return {"success": False, "reason": f"Could not find {side} button", "warning": None}

        random_delay(page, 200, 500)

        # ── Step 5: Fill in the order amount.
        amount_ok = _set_amount(page, order_amount)
        if not amount_ok:
            fallback = page.locator('input[type="text"]').first
            if fallback.is_visible(timeout=1200):
                clear_and_fill(fallback, page, order_amount)
            else:
                return {"success": False, "reason": "Could not locate order amount input", "warning": None}

        # ── Step 6: Take Profit and Stop Loss.
        if take_profit:
            _toggle_and_fill(page, "Take Profit", take_profit)
        if stop_loss:
            _toggle_and_fill(page, "Stop Loss", stop_loss)

        # ── Collect any warning text visible on the form after filling.
        warning_el = page.locator(
            ':text("market is closed"), :text("only pending"), :text("insufficient")'
        ).first
        warning = get_text_if_visible(warning_el, timeout=1200)

        return {"success": True, "reason": None, "warning": warning}

    except Exception as e:
        return {"success": False, "reason": str(e), "warning": None}
