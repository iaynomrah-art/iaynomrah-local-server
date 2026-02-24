import importlib
import os
import threading

# --- Module Imports ---
check_user_module = importlib.import_module("app.automation.ctrader.check-user")
check_user = check_user_module.check_user

place_order_module = importlib.import_module("app.automation.ctrader.place-order")
place_order = place_order_module.place_order

edit_place_order_module = importlib.import_module("app.automation.ctrader.edit-place-order")
edit_place_order = edit_place_order_module.edit_place_order

input_order_module = importlib.import_module("app.automation.ctrader.input-order")
input_order = input_order_module.input_order

_playwright = None
_browser = None
_user_contexts = {}
_user_pages = {}
_browser_lock = threading.Lock()
_session_lock = threading.Lock()

def get_browser():
    """Starts the browser once and keeps it running for future calls."""
    global _playwright, _browser
    with _browser_lock:
        if _playwright is None:
            print("Starting persistent Playwright browser instance...")
            from playwright.sync_api import sync_playwright
            _playwright = sync_playwright().start()
            _browser = _playwright.chromium.launch(
                channel="chrome",
                headless=False  # Set to True when you deploy to production
            )
    return _browser

def run(
    username: str,
    password: str,
    purchase_type: str,
    order_amount: str,
    take_profit: str,
    stop_loss: str,
    account_id: str,
    symbol: str,
    operation: str
):
    global _user_contexts, _user_pages
    # 1. Get the globally running browser (starts it if it's the first run)
    browser = get_browser()
    
    # 2. Define a state file unique to this user
    state_file = f"state_{username}.json"

    try:
        # 3. Check if we already have an active page for this user
        with _session_lock:
            page = _user_pages.get(username)
            context = _user_contexts.get(username)

            if page and not page.is_closed():
                print(f"Reusing existing tab for {username}...")
            else:
                print(f"Creating new context and tab for {username}...")
                # Create a lightweight context, injecting cookies if they exist
                if os.path.exists(state_file):
                    print(f"Injecting saved session for {username}...")
                    context = browser.new_context(storage_state=state_file)
                else:
                    print(f"No saved session for {username}. Creating new context.")
                    context = browser.new_context()

                page = context.new_page()
                _user_contexts[username] = context
                _user_pages[username] = page
        
        print(f"Navigating to cTrader for {username}...")
        page.goto("https://app.ctrader.com", timeout=60000)

        # 1. Wait for the foundational HTML/DOM to finish loading before we start looking for things
        page.wait_for_load_state("domcontentloaded")

        # Check if already logged in by looking for the "Log in" button
        login_button = page.locator('button[type="button"]:has-text("Log in")')
        
        try:
            # 2. Increase the timeout to 20 seconds (20000 ms) to account for slow loading times
            login_button.wait_for(state="visible", timeout=20000)
            
            # "Log in" button is visible — not logged in, need to login
            print("Not logged in. Starting login flow...")
            
            from app.automation.ctrader.login import login
            login(page, username, password)
            
            # Wait for the login process to settle before saving state
            page.wait_for_load_state("networkidle")
            
            # Save the session state for next time
            context.storage_state(path=state_file)
            print("Session state saved successfully.")

        except Exception as e:
            # If 20 seconds pass and the button STILL isn't there, we are genuinely logged in
            print(f"Login button not found or already logged in. Continuing... (Note: {str(e)})")

        # Verify the user and select the correct account
        check_user(page, username, account_id)

        # Route to the correct operation and capture success
        success = False
        match operation:
            case "place-order":
                success = place_order(page, purchase_type, order_amount, symbol, take_profit, stop_loss)
            case "edit-place-order":
                success = edit_place_order(page, purchase_type, order_amount, symbol, take_profit, stop_loss)
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
    except ValueError as ve:
        print(f"VALIDATION ERROR in run_ctrader: {str(ve)}")
        return {
            "status": "error",
            "message": f"Validation failed: {str(ve)}"
        }
    except Exception as e:
        print(f"ERROR in run_ctrader: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "message": f"Automation failed: {str(e)}"
        }
