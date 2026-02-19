from playwright.sync_api import sync_playwright
from app.automation.ctrader.login import login
import importlib

check_user_module = importlib.import_module("app.automation.ctrader.check-user")
check_user = check_user_module.check_user

place_order_module = importlib.import_module("app.automation.ctrader.place-order")
place_order = place_order_module.place_order

edit_place_order_module = importlib.import_module("app.automation.ctrader.edit-place-order")
edit_place_order = edit_place_order_module.edit_place_order

input_order_module = importlib.import_module("app.automation.ctrader.input-order")
input_order = input_order_module.input_order


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
    p = sync_playwright().start()
    browser = p.chromium.launch(
        channel="chrome",
        headless=False
    )
    page = browser.new_page()
    page.goto("https://app.ctrader.com")

    # Check if already logged in by looking for the "Log in" button
    login_button = page.locator('button[type="button"]:has-text("Log in")')
    
    try:
        login_button.wait_for(state="visible", timeout=5000)
        # "Log in" button is visible — not logged in, need to login
        print("Not logged in. Starting login flow...")
        login(page, username, password)
    except:
        # "Log in" button not found — already logged in
        print("Already logged in. Skipping login.")

    # Verify the user and select the correct account
    check_user(page, username, account_id)

    # Route to the correct operation using a switch-case (match)
    match operation:
        case "place-order":
            place_order(page, purchase_type, order_amount, symbol, take_profit, stop_loss)
        case "edit-place-order":
            edit_place_order(page, purchase_type, order_amount, symbol, take_profit, stop_loss)
        case "default" | "1" | _:
            print(f"Operation: {operation} (Default). Running input_order...")
            input_order(page, purchase_type, order_amount, symbol, take_profit, stop_loss)

    return {
        "status": "success",
        "message": f"cTrader automation completed for {symbol} ({operation})",
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