import random
import os
import re
from app.automation.tradelocker._ui import first_visible, click_first, clear_and_fill


def random_delay(page, min_ms=800, max_ms=2500):
    delay = random.randint(min_ms, max_ms)
    page.wait_for_timeout(delay)


def _handle_cookie_banner(page):
    """
    Handles TradeLocker cookie banner if present.
    Cookie preference can be controlled via TRADELOCKER_COOKIE_MODE:
    - mandatory (default)
    - all
    """
    cookie_mode = os.getenv("TRADELOCKER_COOKIE_MODE", "mandatory").strip().lower()

    allow_mandatory = [
        'button:has-text("Allow Mandatory")',
        'button:has-text("Allow mandatory")',
        '[data-testid*="mandatory"]',
    ]
    allow_all = [
        'button:has-text("Allow All")',
        'button:has-text("Allow all")',
        '[data-testid*="allow-all"]',
    ]

    # Try preferred button first, then fallback to the other option.
    preferred = allow_all if cookie_mode == "all" else allow_mandatory
    fallback = allow_mandatory if cookie_mode == "all" else allow_all

    if click_first(page, preferred, timeout=2000, click_timeout=2000):
        print(f"Cookie banner handled via mode='{cookie_mode}'.")
        page.wait_for_timeout(300)
        return

    if click_first(page, fallback, timeout=1200, click_timeout=2000):
        print("Cookie banner handled via fallback option.")
        page.wait_for_timeout(300)
        return

    print("Cookie banner not detected or already dismissed.")


def _set_server(page, server):
    if not server:
        return True

    server_input = first_visible(page, [
        '#server',
        'input[name*="server" i]',
        'input[placeholder*="server" i]',
        '[data-testid*="server"] input',
        'label:has-text("Server") + div input',
        'label:has-text("Server") ~ div input'
    ], timeout=4000)

    if not server_input:
        return False

    clear_and_fill(server_input, page, server)
    page.wait_for_timeout(400)

    server_pick = first_visible(page, [
        f'text="{server}"',
        f':text-is("{server}")',
        f'[role="option"]:has-text("{server}")',
        f'[data-testid*="server"]:has-text("{server}")'
    ], timeout=2000)

    if server_pick:
        try:
            server_pick.click(timeout=1500)
        except Exception:
            pass

    return True


def dismiss_post_login_overlays(page):
    """Best-effort cleanup of TradeLocker overlays that can block automation."""
    # Cookie/privacy consent modal inside authenticated workspace.
    if click_first(page, [
        'button:has-text("Accept")',
        'button:has-text("Allow Mandatory")',
        'button:has-text("Allow mandatory")',
        'button:has-text("Allow All")',
        'button:has-text("Allow all")',
        '[role="dialog"] button:has-text("Accept")',
        '[aria-modal="true"] button:has-text("Accept")',
    ], timeout=1600, click_timeout=1800):
        print("Closed cookie/privacy overlay.")
        page.wait_for_timeout(300)

    # Product update modal (e.g., "What's new").
    for _ in range(3):
        closed = click_first(page, [
            'button[aria-label*="close" i]',
            'button:has-text("Close")',
            'button:has-text("Skip")',
            '[role="dialog"] button[class*="close" i]',
            '[role="dialog"] [data-testid*="close" i]',
            '[aria-modal="true"] [data-testid*="close" i]',
        ], timeout=1200, click_timeout=1500)

        if closed:
            print("Closed post-login update overlay.")
            page.wait_for_timeout(250)
            continue

        try:
            page.keyboard.press("Escape")
            page.wait_for_timeout(180)
        except Exception:
            pass
        break


def login(page, username, password, server=None):
    if not password:
        return {"success": False, "reason": "Password is required for first-time TradeLocker login", "warning": None}

    random_delay(page, 300, 900)

    _handle_cookie_banner(page)

    click_first(page, [
        'button:has-text("Log in")',
        'button:has-text("Sign in")',
        'a:has-text("Log in")',
        'a:has-text("Sign in")'
    ], timeout=4000)

    user_input = first_visible(page, [
        '#email',
        'input[type="email"]',
        'input[name="email"]',
        'input[name="username"]',
        'input[placeholder*="email" i]',
        'input[placeholder*="username" i]'
    ], timeout=12000)

    if not user_input:
        return {"success": False, "reason": "Could not find TradeLocker username/email input", "warning": None}

    clear_and_fill(user_input, page, username)

    random_delay(page, 300, 800)

    pass_input = first_visible(page, [
        '#password',
        'input[type="password"]',
        'input[name="password"]',
        'input[placeholder*="password" i]'
    ], timeout=8000)

    if not pass_input:
        return {"success": False, "reason": "Could not find TradeLocker password input", "warning": None}

    clear_and_fill(pass_input, page, password)

    random_delay(page, 200, 500)

    if server and not _set_server(page, server):
        return {"success": False, "reason": "Could not find TradeLocker server field", "warning": None}

    random_delay(page, 300, 800)

    submitted = False

    # Keycloak-like pages may render submit as <input type="submit">, not a <button>.
    submit = first_visible(page, [
        'button:has-text("Log In")',
        '[role="button"]:has-text("Log In")',
        'button:has-text("Log in")',
        'button:has-text("Sign in")',
        'button[type="submit"]',
        'input[type="submit"]',
        'input[id*="login" i]',
        'input[name*="login" i]',
        '[data-testid*="login" i]'
    ], timeout=6000)

    if submit:
        try:
            submit.click(timeout=5000)
            submitted = True
        except Exception:
            submitted = False

    if not submitted:
        try:
            role_submit = page.get_by_role("button", name=re.compile(r"^(log\s*in|sign\s*in)$", re.I)).first
            role_submit.click(timeout=3000)
            submitted = True
        except Exception:
            submitted = False

    if not submitted:
        try:
            pass_input.press("Enter", timeout=2000)
            submitted = True
        except Exception:
            submitted = False

    if not submitted:
        return {"success": False, "reason": "Could not trigger TradeLocker login submit action", "warning": None}

    try:
        page.wait_for_selector(
            ':text("Positions"), :text("Orders"), :text("Portfolio"), :text("Account"), [data-testid*="positions"]',
            timeout=20000
        )
        dismiss_post_login_overlays(page)
        return {"success": True, "reason": None, "warning": None}
    except Exception:
        return {"success": False, "reason": "Login submitted but dashboard indicators did not appear", "warning": "Check MFA, captcha, or credential validity"}
