import importlib
import json
import os
import threading
from pathlib import Path
from app.automation.tradelocker.login import dismiss_post_login_overlays

# --- Module Imports ---
check_user_module = importlib.import_module("app.automation.tradelocker.check-user")
check_user = check_user_module.check_user

place_order_module = importlib.import_module("app.automation.tradelocker.place-order")
place_order_click = place_order_module.place_order
full_place_order = place_order_module.full_place_order

edit_place_order_module = importlib.import_module("app.automation.tradelocker.edit-place-order")
edit_place_order = edit_place_order_module.edit_place_order

input_order_module = importlib.import_module("app.automation.tradelocker.input-order")
input_order = input_order_module.input_order

trade_terminator_module = importlib.import_module("app.automation.tradelocker.trade-terminator")
terminate_trade = trade_terminator_module.terminate_trade

close_position_module = importlib.import_module("app.automation.tradelocker.close-position")
close_position = close_position_module.close_position

_playwright = None
_user_contexts = {}
_user_pages = {}
_lock = threading.Lock()


def get_playwright():
    """Starts the playwright instance if not already started."""
    global _playwright
    if _playwright is None:
        from playwright.sync_api import sync_playwright
        _playwright = sync_playwright().start()
    return _playwright


def _cleanup_user(username: str):
    """Cleans up cached context and page for a user."""
    global _user_contexts, _user_pages
    print(f"Cleaning up cached browser state for {username}...")
    _user_contexts.pop(username, None)
    _user_pages.pop(username, None)


def _fix_chrome_exit_type(profile_dir):
    """
    Patches Chrome preference files to mark the previous session as clean.
    Prevents restore dialogs from blocking automation.
    """
    default_dir = Path(profile_dir) / "Default"

    for pref_file_name in ["Preferences", "Secure Preferences"]:
        pref_file = default_dir / pref_file_name
        if pref_file.exists():
            try:
                data = json.loads(pref_file.read_text(encoding="utf-8"))
                if "profile" not in data:
                    data["profile"] = {}
                data["profile"]["exit_type"] = "Normal"
                data["profile"]["exited_cleanly"] = True
                pref_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
            except Exception as e:
                print(f"Could not patch {pref_file_name}: {e}")


def get_user_context(username: str):
    """Gets or creates a persistent context for the specific user."""
    global _user_contexts

    if username in _user_contexts:
        context = _user_contexts[username]
        try:
            if context.browser and context.browser.is_connected():
                return context
        except Exception:
            pass

        print(f"Context for {username} is stale or closed. Re-initializing...")
        _cleanup_user(username)

    pw = get_playwright()

    base_dir = Path(__file__).resolve().parent.parent.parent.parent
    profile_dir = base_dir / "tradelocker_profile" / username
    profile_dir.mkdir(parents=True, exist_ok=True)

    _fix_chrome_exit_type(profile_dir)

    print(f"Launching TradeLocker context for {username} at {profile_dir}...")

    context = pw.chromium.launch_persistent_context(
        user_data_dir=str(profile_dir),
        channel="chrome",
        headless=False,
        viewport={"width": 1360, "height": 720},
        args=[
            "--start-maximized",
            "--no-zygote",
            "--disable-gpu",
            "--disable-infobars",
            "--no-default-browser-check",
            "--no-first-run",
            "--disable-extensions",
            "--disable-session-crashed-bubble",
            "--disable-notifications",
            "--hide-scrollbars",
            "--mute-audio",
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-accelerated-2d-canvas"
        ]
    )

    context.on("close", lambda _: _cleanup_user(username))

    _user_contexts[username] = context
    return context


def maximize_browser_window(page):
    """Maximize browser window for better TradeLocker visibility."""
    try:
        session = page.context.new_cdp_session(page)
        target = session.send("Browser.getWindowForTarget")
        window_id = target.get("windowId")
        if window_id:
            session.send(
                "Browser.setWindowBounds",
                {"windowId": window_id, "bounds": {"windowState": "maximized"}},
            )
            return True
    except Exception as e:
        print(f"Could not maximize via CDP: {e}")

    try:
        # Fallback in case CDP window control is unavailable.
        page.set_viewport_size({"width": 1920, "height": 1080})
        return True
    except Exception:
        return False


def ensure_tradelocker_loaded(page, url: str):
    """Navigates to TradeLocker and retries load on frontend hydration failures."""
    readiness = page.locator(
        '#email, #password, #server, '
        'button:has-text("Log In"), button:has-text("Log in"), button:has-text("Sign in"), '
        'button:has-text("Allow Mandatory"), button:has-text("Allow All"), '
        ':text("Positions"), :text("Orders"), :text("Account"), '
        '[data-testid*="positions"], [data-testid*="orders"]'
    )

    print(f"Navigating to {url}...")

    try:
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        readiness.first.wait_for(state="visible", timeout=45000)
        print("TradeLocker UI loaded on first try.")
        return True
    except Exception:
        print("Initial load failed. Trying API reload...")

    try:
        page.reload(wait_until="domcontentloaded", timeout=45000)
        readiness.first.wait_for(state="visible", timeout=30000)
        print("TradeLocker UI loaded after API reload.")
        return True
    except Exception:
        print("API reload failed. Trying hard refresh...")

    try:
        page.mouse.click(10, 10)
        page.wait_for_timeout(500)
        page.keyboard.press("Control+Shift+R")
        readiness.first.wait_for(state="visible", timeout=40000)
        print("TradeLocker UI loaded after hard refresh.")
        return True
    except Exception as e:
        print(f"TradeLocker failed to render after retries: {e}")
        return False


def is_tradelocker_logged_in(page) -> bool:
    """Best-effort check that user is on authenticated TradeLocker workspace."""
    try:
        # Strong signal: workspace tabs are visible after auth.
        workspace = page.locator(
            ':text("Positions"), :text("Orders"), :text("Account"), [data-testid*="positions"], [data-testid*="orders"]'
        ).first
        if workspace.is_visible(timeout=1500):
            return True
    except Exception:
        pass

    # If auth form is visible, we are definitely not logged in yet.
    try:
        auth_field = page.locator('#email, #password, #server').first
        if auth_field.is_visible(timeout=800):
            return False
    except Exception:
        pass

    current_url = (page.url or "").lower()
    if "auth.tradelocker.com" in current_url:
        return False

    return False


def ensure_positions_tab(page):
    """Best-effort switch to Positions tab in the bottom workspace panel."""
    tab_selectors = [
        'div[role="tab"]:has-text("Positions")',
        'button:has-text("Positions")',
        'a:has-text("Positions")',
        ':text("Positions")',
    ]

    for selector in tab_selectors:
        try:
            tab = page.locator(selector).first
            if not tab.is_visible(timeout=900):
                continue

            tab.click(timeout=1500)
            page.wait_for_timeout(200)
            print("Ensured TradeLocker is on Positions tab.")
            return True
        except Exception:
            continue

    return False


def run(
    username: str,
    operation: str,
    password: str = None,
    server: str = None,
    purchase_type: str = None,
    order_amount: str = None,
    take_profit: str = None,
    stop_loss: str = None,
    account_id: str = None,
    db_account_id: str = None,
    symbol: str = None
):
    global _user_pages

    with _lock:
        try:
            context = get_user_context(username)
            page = _user_pages.get(username)

            if page and page.is_closed():
                page = None

            if not page:
                try:
                    if context.pages:
                        page = context.pages[0]
                        print(f"Found existing tab for {username}. Reusing...")
                    else:
                        print(f"Creating new tab for {username}...")
                        page = context.new_page()
                except Exception as e:
                    if "Target closed" in str(e) or "context has been closed" in str(e):
                        print(f"Context closed unexpectedly for {username}. Retrying...")
                        _cleanup_user(username)
                        context = get_user_context(username)
                        page = context.new_page()
                    else:
                        raise e

                _user_pages[username] = page

            try:
                page.bring_to_front()
            except Exception as e:
                if "Target closed" in str(e):
                    page = context.new_page()
                    _user_pages[username] = page
                    page.bring_to_front()
                else:
                    raise e

            maximize_browser_window(page)

            current_url = page.url or ""
            if "tradelocker" not in current_url.lower():
                platform_url = os.getenv("TRADELOCKER_URL", "https://demo.tradelocker.com/en/trade")
                if not ensure_tradelocker_loaded(page, platform_url):
                    raise Exception("TradeLocker failed to load properly after multiple attempts.")
            else:
                print(f"Already on TradeLocker for {username}. Reusing current page state.")

            if is_tradelocker_logged_in(page):
                ensure_positions_tab(page)

            login_result = {"success": True}
            login_button = page.locator('button:has-text("Log in"), button:has-text("Sign in"), a:has-text("Log in"), a:has-text("Sign in")').first

            if operation == "login-only":
                from app.automation.tradelocker.login import login as login_flow

                if is_tradelocker_logged_in(page):
                    ensure_positions_tab(page)
                    return {
                        "status": "success",
                        "message": "TradeLocker automation completed for None (login-only)",
                        "confirmed": True,
                        "details": {
                            "account_id": account_id,
                            "symbol": symbol,
                            "operation": operation,
                            "purchase_type": purchase_type,
                            "order_amount": order_amount,
                            "take_profit": take_profit,
                            "stop_loss": stop_loss,
                        },
                        "reason": "TradeLocker already logged in",
                    }

                login_result = login_flow(page, username, password, server)
                if isinstance(login_result, dict) and not login_result.get("success", False):
                    return {
                        "status": "failed",
                        "message": login_result.get("reason", "TradeLocker login failed"),
                        "confirmed": False,
                        "details": {
                            "account_id": account_id,
                            "symbol": symbol,
                            "operation": operation,
                            "purchase_type": purchase_type,
                            "order_amount": order_amount,
                            "take_profit": take_profit,
                            "stop_loss": stop_loss,
                        },
                        "reason": login_result.get("reason"),
                        "warning": login_result.get("warning"),
                    }

                page.wait_for_timeout(1500)
                if not is_tradelocker_logged_in(page):
                    return {
                        "status": "failed",
                        "message": "Login submitted but authenticated workspace was not detected",
                        "confirmed": False,
                        "details": {
                            "account_id": account_id,
                            "symbol": symbol,
                            "operation": operation,
                            "purchase_type": purchase_type,
                            "order_amount": order_amount,
                            "take_profit": take_profit,
                            "stop_loss": stop_loss,
                        },
                        "reason": "TradeLocker login not verified",
                        "warning": "Check captcha, MFA, credentials, or server selection",
                    }

                ensure_positions_tab(page)

                return {
                    "status": "success",
                    "message": "TradeLocker automation completed for None (login-only)",
                    "confirmed": True,
                    "details": {
                        "account_id": account_id,
                        "symbol": symbol,
                        "operation": operation,
                        "purchase_type": purchase_type,
                        "order_amount": order_amount,
                        "take_profit": take_profit,
                        "stop_loss": stop_loss,
                    },
                    "reason": "TradeLocker login verified",
                }

            try:
                login_button.wait_for(state="visible", timeout=5000)
                print("Not logged in. Starting TradeLocker login flow...")

                from app.automation.tradelocker.login import login as login_flow
                login_result = login_flow(page, username, password, server)
                if isinstance(login_result, dict) and not login_result.get("success", False):
                    return {
                        "status": "failed",
                        "message": login_result.get("reason", "TradeLocker login failed"),
                        "confirmed": False,
                        "details": {
                            "account_id": account_id,
                            "symbol": symbol,
                            "operation": operation,
                            "purchase_type": purchase_type,
                            "order_amount": order_amount,
                            "take_profit": take_profit,
                            "stop_loss": stop_loss,
                        },
                        "reason": login_result.get("reason"),
                        "warning": login_result.get("warning"),
                    }

                page.wait_for_load_state("networkidle")
                print("TradeLocker login flow completed.")
            except Exception:
                print("No login button detected. Assuming active session.")

            # Ensure modals are closed before account switching or order actions.
            dismiss_post_login_overlays(page)
            ensure_positions_tab(page)

            check_user(page, username, account_id)

            result = None
            match operation:
                case "place-order":
                    result = place_order_click(page)
                case "auto-place-order":
                    result = full_place_order(page, purchase_type, order_amount, symbol, take_profit, stop_loss)
                case "auto-place-and-terminate":
                    place_result = full_place_order(page, purchase_type, order_amount, symbol, take_profit, stop_loss)
                    is_success = place_result.get("success", False) if isinstance(place_result, dict) else bool(place_result)
                    if is_success:
                        result = terminate_trade(page, symbol, account_id, db_account_id)
                    else:
                        result = place_result
                case "place-and-terminate":
                    place_result = place_order_click(page)
                    is_success = place_result.get("success", False) if isinstance(place_result, dict) else bool(place_result)
                    if is_success:
                        result = terminate_trade(page, symbol, account_id, db_account_id)
                    else:
                        result = place_result
                case "edit-place-order":
                    result = edit_place_order(page, purchase_type, order_amount, symbol, take_profit, stop_loss)
                case "input-order":
                    result = input_order(page, purchase_type, order_amount, symbol, take_profit, stop_loss)
                case "trade-terminator":
                    result = terminate_trade(page, symbol, account_id, db_account_id)
                case "close-position":
                    result = close_position(page, symbol)
                case "default" | "1" | _:
                    result = input_order(page, purchase_type, order_amount, symbol, take_profit, stop_loss)

            if isinstance(result, bool):
                success = result
                reason = None
                warning = None
            elif isinstance(result, dict):
                success = result.get("success", False)
                reason = result.get("reason")
                warning = result.get("warning")
            else:
                success = False
                reason = "Unknown result format"
                warning = None

            fail_reason = reason or f"Operation '{operation}' did not return a confirmed success status."

            response = {
                "status": "success" if success else "failed",
                "message": f"TradeLocker automation completed for {symbol} ({operation})" if success else fail_reason,
                "confirmed": success,
                "details": {
                    "account_id": account_id,
                    "symbol": symbol,
                    "operation": operation,
                    "purchase_type": purchase_type,
                    "order_amount": order_amount,
                    "take_profit": take_profit,
                    "stop_loss": stop_loss,
                }
            }

            if reason:
                response["reason"] = reason
            if warning:
                response["warning"] = warning

            return response

        except Exception as e:
            msg = str(e)
            print(f"ERROR in run_tradelocker for {username}: {msg}")

            if "Target page, context or browser has been closed" in msg or "Target closed" in msg:
                _cleanup_user(username)

            return {
                "status": "error",
                "message": f"Automation failed: {msg}"
            }
