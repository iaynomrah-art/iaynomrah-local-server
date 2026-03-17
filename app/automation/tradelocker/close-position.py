def close_position(page, symbol: str) -> dict:
    """
    Attempts to close an open position for the provided symbol.
    """
    if not symbol:
        return {"success": False, "reason": "symbol is required for close-position", "warning": None}

    try:
        # Ensure positions tab/section is active.
        for selector in [
            'button:has-text("Positions")',
            'div[role="tab"]:has-text("Positions")',
            ':text("Positions")',
            'button:has-text("Open Positions")'
        ]:
            try:
                tab = page.locator(selector).first
                if tab.is_visible(timeout=800):
                    tab.click(timeout=1500)
                    break
            except Exception:
                continue

        symbol_text = str(symbol).strip().upper()
        positions_panel = page.locator(
            'div:has-text("Positions"):has-text("Closed Positions"), div:has-text("Positions"):has-text("Instrument")'
        ).first

        row = None
        try:
            if positions_panel.is_visible(timeout=1000):
                row = positions_panel.locator(
                    f'tr:has-text("{symbol_text}"), div[role="row"]:has-text("{symbol_text}"), div:has-text("{symbol_text}")'
                ).first
        except Exception:
            row = None

        if not row:
            row = page.locator(
                f'tr:has-text("{symbol_text}"), div[role="row"]:has-text("{symbol_text}"), div:has-text("{symbol_text}")'
            ).first
        if not row.is_visible(timeout=3000):
            return {
                "success": False,
                "reason": f"No active TradeLocker position found for {symbol}",
                "warning": "Position may already be closed"
            }

        # Prefer explicit close icon/action button in the row.
        # Codegen says: getByRole('button', { name: 'Close position', exact: true })
        close_btn = None
        clicked = False

        # Strategy 1: The exact button name seen in codegen
        try:
            btn = row.get_by_role("button", name="Close position", exact=True).first
            if btn.is_visible(timeout=1000):
                btn.click(timeout=2000)
                clicked = True
                print(f"[close-position] Clicked exact 'Close position' button.")
        except Exception:
            pass

        # Strategy 2: Fallback to old heuristic icon selectors
        if not clicked:
            try:
                candidate = row.locator(
                    'button:has-text("Close"), [aria-label*="close" i], [title*="close" i], [data-testid*="close" i], [data-testid*="remove" i], [data-testid*="x" i]'
                ).first
                if candidate.is_visible(timeout=1000):
                    candidate.click(timeout=2000)
                    clicked = True
                    print(f"[close-position] Clicked heuristic close button.")
            except Exception:
                pass

        # Strategy 3: Fallback for icon-only actions columns where semantic labels are missing.
        if not clicked:
            try:
                action_buttons = row.locator("button")
                count = action_buttons.count()
                if count > 0:
                    action_buttons.nth(count - 1).click(timeout=1800)
                    clicked = True
                    print(f"[close-position] Clicked last button in row as fallback.")
            except Exception:
                pass

        # Final fallback: use global Close All flow.
        if not clicked:
            close_all = page.locator('button:has-text("Close All"), [data-testid*="close-all" i]').first
            if close_all.is_visible(timeout=1200):
                close_all.click(timeout=1500)
                clicked = True

        if not clicked:
            return {"success": False, "reason": f"Could not locate close action for {symbol}", "warning": None}

        confirm_btn = page.locator('button:has-text("Confirm"), button:has-text("Close"), button:has-text("Yes"), button:has-text("OK")').first
        try:
            if confirm_btn.is_visible(timeout=1200):
                confirm_btn.click(timeout=1500)
        except Exception:
            pass

        return {"success": True, "reason": None, "warning": None}

    except Exception as e:
        return {"success": False, "reason": str(e), "warning": None}
