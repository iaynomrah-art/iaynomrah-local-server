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

def get_user_context(username: str):
    """Gets or creates a persistent context for the specific user."""
    global _user_contexts
    
    if username in _user_contexts:
        return _user_contexts[username]

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
    
    _user_contexts[username] = context
    return context

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
                existing_pages = context.pages
                if existing_pages:
                    page = existing_pages[0]
                    print(f"Found existing tab for {username}. Reusing...")
                else:
                    print(f"Creating new tab for {username}...")
                    page = context.new_page()
                
                _user_pages[username] = page

            # 3. Bring to front and navigate
            page.bring_to_front()
            
            # Only navigate if we aren't already on cTrader or if we are on a blank page
            current_url = page.url
            if "ctrader.com" not in current_url:
                print(f"Navigating to cTrader for {username}...")
                page.goto("https://app.ctrader.com", timeout=60000)
                page.wait_for_load_state("domcontentloaded")
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
            print(f"ERROR in run_ctrader for {username}: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "message": f"Automation failed: {str(e)}"
            }
