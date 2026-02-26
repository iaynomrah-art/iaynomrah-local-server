import importlib
import os
import threading
from pathlib import Path

# --- Module Imports ---
check_user_module = importlib.import_module("app.automation.ctrader.check-user")
check_user = check_user_module.check_user

place_order_module = importlib.import_module("app.automation.ctrader.place-order")
place_order_click = place_order_module.place_order
full_place_order = place_order_module.full_place_order

edit_place_order_module = importlib.import_module("app.automation.ctrader.edit-place-order")
edit_place_order = edit_place_order_module.edit_place_order

input_order_module = importlib.import_module("app.automation.ctrader.input-order")
input_order = input_order_module.input_order

_playwright = None
_user_contexts = {}  # Map username -> persistent context
_user_pages = {}     # Map username -> active page
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

def get_user_context(username: str):
    """Gets or creates a persistent context for the specific user."""
    global _user_contexts
    
    if username in _user_contexts:
        context = _user_contexts[username]
        # Check if the context is still usable
        try:
            # A simple way to check if the browser is still connected
            if context.browser and context.browser.is_connected():
                return context
        except Exception:
            pass
        
        # If we reach here, the context is likely stale
        print(f"Context for {username} is stale or closed. Re-initializing...")
        _cleanup_user(username)

    pw = get_playwright()
    
    # Define absolute path for the profile directory
    base_dir = Path(__file__).resolve().parent.parent.parent.parent
    profile_dir = base_dir / "ctrader_profile" / username
    profile_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Launching persistent context for {username} at {profile_dir}...")
    
    context = pw.chromium.launch_persistent_context(
        user_data_dir=str(profile_dir),
        channel="chrome",
        headless=False,  # Set to True for production server
        args=[
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-accelerated-2d-canvas",
            "--no-first-run",
            "--no-zygote",
            "--disable-gpu"
        ]
    )
    
    # Register close handler to cleanup when browser is closed manually
    context.on("close", lambda ctx: _cleanup_user(username))
    
    _user_contexts[username] = context
    return context


def ensure_ctrader_loaded(page, url="https://app.ctrader.com"):
    """
    Navigates to cTrader and aggressively forces reloads if the SPA framework hangs.
    """
    print(f"Navigating to {url}...")
    
    # --- ATTEMPT 1: Standard Navigation ---
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=45000)
        print("Waiting for cTrader to render (checking for Login screen or Workspace)...")
        indicator = page.locator('button[type="button"]:has-text("Log in"), text="Positions"').first
        indicator.wait_for(state="visible", timeout=15000)
        print("  ✓ cTrader UI loaded successfully on the first try.")
        return True
    except Exception:
        print("  ⏳ Attempt 1 failed. Initiating API reload...")

    # --- ATTEMPT 2: Playwright API Reload ---
    try:
        page.reload(wait_until="domcontentloaded", timeout=30000)
        indicator = page.locator('button[type="button"]:has-text("Log in"), text="Positions"').first
        indicator.wait_for(state="visible", timeout=15000)
        print("  ✓ cTrader UI loaded successfully after API reload.")
        return True
    except Exception:
        print("  ⏳ Attempt 2 failed. Forcing raw keyboard reload (Ctrl + Shift + R)...")

    # --- ATTEMPT 3: Keyboard Force Reload (The "Ctrl+R" bypass) ---
    try:
        # Click the top-left corner to ensure the web page has OS-level focus
        page.mouse.click(10, 10)
        page.wait_for_timeout(500)
        
        # Use Ctrl+Shift+R for a hard, cache-clearing refresh
        page.keyboard.press("Control+Shift+R")
        
        # Because we bypassed Playwright's navigation logic, we just wait for the element to appear
        indicator = page.locator('button[type="button"]:has-text("Log in"), text="Positions"').first
        indicator.wait_for(state="visible", timeout=25000)
        print("  ✓ cTrader UI loaded successfully after Ctrl+Shift+R force reload.")
        return True
    except Exception as e:
        print(f"  ✗ Critical failure: cTrader completely failed to render. Error: {e}")
        return False

def run(
    username: str,
    operation: str,
    password: str = None,
    purchase_type: str = None,
    order_amount: str = None,
    take_profit: str = None,
    stop_loss: str = None,
    account_id: str = None,
    symbol: str = None
):
    global _user_pages
    
    with _lock:
        try:
            # 1. Get the persistent context for this user
            context = get_user_context(username)
            
            # 2. Check if we already have an active page, or find one in the context
            page = _user_pages.get(username)
            
            # If the stored page is closed, try to grab an existing page from context (if any)
            if page and page.is_closed():
                page = None
            
            if not page:
                try:
                    existing_pages = context.pages
                    if existing_pages:
                        page = existing_pages[0]
                        print(f"Found existing tab for {username}. Reusing...")
                    else:
                        print(f"Creating new tab for {username}...")
                        page = context.new_page()
                except Exception as e:
                    if "Target closed" in str(e) or "context has been closed" in str(e):
                        print(f"Context closed unexpectedly for {username}. Retrying with new context...")
                        _cleanup_user(username)
                        context = get_user_context(username)
                        page = context.new_page()
                    else:
                        raise e
                
                _user_pages[username] = page

            # 3. Bring to front and navigate
            try:
                page.bring_to_front()
            except Exception as e:
                if "Target closed" in str(e):
                    print(f"Page closed unexpectedly for {username}. Re-creating...")
                    page = context.new_page()
                    _user_pages[username] = page
                    page.bring_to_front()
                else:
                    raise e
            
            # Only navigate if we aren't already on cTrader or if we are on a blank page
            current_url = page.url
            if "ctrader.com" not in current_url:
                print(f"Navigating to cTrader for {username}...")
                # --- NEW SMART LOAD LOGIC ---
                if not ensure_ctrader_loaded(page):
                    raise Exception("cTrader failed to load properly after multiple attempts.")
            else:
                print(f"Already on cTrader for {username}. Reusing current page state.")

            # 4. Check login status
            # If we are in a persistent context, we might already be logged in
            login_button = page.locator('button[type="button"]:has-text("Log in")')
            
            try:
                # Wait briefly to see if login button appears (meaning we are NOT logged in)
                login_button.wait_for(state="visible", timeout=5000)
                print("Not logged in. Starting login flow...")
                
                from app.automation.ctrader.login import login as login_flow
                login_flow(page, username, password)
                
                # Wait for navigation/dashboard
                page.wait_for_load_state("networkidle")
                print("Login flow completed.")
            except Exception:
                # If timeout or not visible, assume we are logged in
                print("No login button detected. Assuming already logged in via persistent session.")

            # 5. Verify the user and select the correct account
            check_user(page, username, account_id)

            # 6. Route to the correct operation
            success = False
            match operation:
                case "place-order":
                    success = place_order_click(page)
                case "auto-place-order":
                    success = full_place_order(page, purchase_type, order_amount, symbol, take_profit, stop_loss)
                case "edit-place-order":
                    success = edit_place_order(page, purchase_type, order_amount, symbol, take_profit, stop_loss)
                case "input-order":
                    success = input_order(page, purchase_type, order_amount, symbol, take_profit, stop_loss)
                case "default" | "1" | _:
                    print(f"Operation: {operation} (Default). Running input_order...")
                    success = input_order(page, purchase_type, order_amount, symbol, take_profit, stop_loss)

            if not success:
                print(f"WARNING: Operation '{operation}' did not return a confirmed success status.")

            return {
                "status": "success",
                "message": f"cTrader automation completed for {symbol} ({operation})",
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

        except Exception as e:
            msg = str(e)
            print(f"ERROR in run_ctrader for {username}: {msg}")
            
            # If it's a closure error, cleanup so the next attempt starts fresh
            if "Target page, context or browser has been closed" in msg or "Target closed" in msg:
                _cleanup_user(username)
                
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "message": f"Automation failed: {msg}"
            }