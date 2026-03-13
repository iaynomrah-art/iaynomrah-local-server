import random
from app.automation.tradelocker._ui import click_first, first_visible


def random_delay(page, min_ms=800, max_ms=2500):
    delay = random.randint(min_ms, max_ms)
    page.wait_for_timeout(delay)


def _open_bottom_left_account_drawer(page):
    """Open TradeLocker account drawer from the bottom-left profile/avatar area."""
    selectors = [
        # Avatar/profile trigger at bottom-left rail.
        'button[aria-label*="account" i]',
        'button[aria-label*="profile" i]',
        '[data-testid*="account-switcher" i]',
        '[data-testid*="profile" i]',
        # Drawer-specific text appears after opening.
        ':text("Trading account")',
    ]

    opened = click_first(page, selectors, timeout=1600, click_timeout=1800)
    if opened:
        page.wait_for_timeout(250)
        return True

    # Last-resort click near bottom-left where avatar usually lives.
    try:
        page.mouse.click(24, 690)
        page.wait_for_timeout(300)
        return True
    except Exception:
        return False


def _select_account_id_from_drawer(page, account_id):
    account_text = str(account_id).strip().lstrip("#")

    # Prefer row that contains full account header like "#1989349".
    row_candidates = [
        f'div:has-text("#{account_text}")',
        f'span:has-text("#{account_text}")',
        f'div:has-text("{account_text}")',
        f'span:has-text("{account_text}")',
    ]

    for selector in row_candidates:
        try:
            row = page.locator(selector).first
            if row.is_visible(timeout=1800):
                row.click(timeout=2200)
                page.wait_for_timeout(250)
                return True
        except Exception:
            continue

    return False


def check_user(page, username, account_id):
    """
    Opens account switcher and selects the requested account_id.
    Raises ValueError if account_id is missing or cannot be found.
    """
    if not account_id:
        raise ValueError("TradeLocker account_id is required")

    random_delay(page, 600, 1200)

    switcher_selectors = [
        'button[aria-label*="account" i]',
        'button:has-text("Account")',
        'button:has-text("Accounts")',
        '[data-testid*="account"]',
        'div:has-text("Account")'
    ]

    # First choice: bottom-left account drawer used by current TradeLocker UI.
    opened = _open_bottom_left_account_drawer(page)

    # Fallback: legacy account switcher controls.
    if not opened:
        opened = click_first(page, switcher_selectors, timeout=1200, click_timeout=2000)

    if not opened:
        print("Account switcher not explicitly opened; trying direct account lookup.")

    random_delay(page, 400, 900)

    # Primary selection path for drawer UI.
    if _select_account_id_from_drawer(page, account_id):
        print(f"Selected TradeLocker account: {account_id}")
        return

    account_text = str(account_id).strip()
    account_candidates = [
        f'text="{account_text}"',
        f'text="#{account_text.lstrip("#")}"',
        f':text-is("{account_text}")',
        f'span:has-text("{account_text}")',
        f'div:has-text("{account_text}")',
        f'[data-testid*="account"]:has-text("{account_text}")',
    ]

    for selector in account_candidates:
        candidate = first_visible(page, [selector], timeout=2500)
        if candidate:
            try:
                candidate.click(timeout=2500)
                random_delay(page, 300, 700)
                print(f"Selected TradeLocker account: {account_id}")
                return
            except Exception:
                continue

    raise ValueError(f"TradeLocker account ID '{account_id}' not found in account switcher")
