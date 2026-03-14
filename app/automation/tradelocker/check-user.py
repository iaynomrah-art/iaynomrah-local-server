import random


def random_delay(page, min_ms=800, max_ms=2500):
    delay = random.randint(min_ms, max_ms)
    page.wait_for_timeout(delay)


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


def click_first(page, selectors, timeout=3000, click_timeout=2000):
    """Click the first visible element from selectors."""
    target = first_visible(page, selectors, timeout=timeout)
    if not target:
        return False
    try:
        target.click(timeout=click_timeout)
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Account drawer helpers
# ---------------------------------------------------------------------------

def _open_bottom_left_profile(page):
    """
    Click the bottom-left profile/avatar button to open the account drawer.
    Only uses the profile button area — no coordinate guessing of other UI zones.
    """
    selectors = [
        # Primary: avatar/account button in the bottom-left nav rail.
        'button[aria-label*="account" i]',
        'button[aria-label*="profile" i]',
        '[data-testid*="account-switcher" i]',
        '[data-testid*="profile" i]',
        # Fallback: visible text that appears in the closed-state button.
        'button:has-text("Trading account")',
        'button:has-text("Account")',
    ]

    opened = click_first(page, selectors, timeout=2000, click_timeout=2000)
    if opened:
        page.wait_for_timeout(400)
        return True

    # Last-resort: click the very bottom-left corner where the avatar lives.
    # This is intentionally limited to a tight region (not timezone or other UI).
    try:
        page.mouse.click(26, 690)
        page.wait_for_timeout(400)
        return True
    except Exception:
        return False


def _close_drawer(page):
    """Close the account drawer by pressing Escape, then clicking into the chart."""
    try:
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)
    except Exception:
        pass

    # Click into the chart canvas area to dismiss any remaining overlay.
    try:
        page.mouse.click(350, 200)
        page.wait_for_timeout(200)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def check_user(page, username, account_id):
    """
    Opens the bottom-left account drawer, verifies the requested account_id
    is listed, then clicks outside to close the drawer.

    Does NOT switch accounts — just confirms presence.
    Logs a warning (does NOT raise) if the account cannot be found.
    """
    if not account_id:
        print("WARNING: No account_id provided – skipping account check.")
        return

    random_delay(page, 400, 800)

    opened = _open_bottom_left_profile(page)
    if not opened:
        print(f"WARNING: Could not open account drawer to verify account '{account_id}'.")
        return

    random_delay(page, 300, 600)

    # Check if the account ID is visible inside the drawer.
    account_text = str(account_id).strip().lstrip("#")
    found = False

    for selector in [
        f'div:has-text("#{account_text}")',
        f'span:has-text("#{account_text}")',
        f'li:has-text("#{account_text}")',
        f'div:has-text("{account_text}")',
        f'span:has-text("{account_text}")',
    ]:
        try:
            el = page.locator(selector).first
            if el.is_visible(timeout=1500):
                found = True
                break
        except Exception:
            continue

    if found:
        print(f"Verified TradeLocker account: #{account_text}")
    else:
        print(f"WARNING: TradeLocker account ID '{account_id}' not found in drawer. "
              "Continuing with currently selected account.")

    # Close the drawer – click outside, do NOT click any account row.
    _close_drawer(page)
    
    # Wait 3 seconds (3000ms) after clicking outside to ensure the drawer is fully closed
    page.wait_for_timeout(3000)
