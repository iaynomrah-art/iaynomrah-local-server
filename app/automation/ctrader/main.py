from playwright.sync_api import sync_playwright
from app.automation.ctrader.login import login
import importlib

check_user_module = importlib.import_module("app.automation.ctrader.check-user")
check_user = check_user_module.check_user


def run(
    username: str,
    password: str,
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

    login(page, username, password)

    # Verify the user and select the correct account
    check_user(page, username, account_id)

    return {
        "status": "success",
        "message": f"cTrader automation completed for {symbol} ({operation})",
        "details": {
            "account_id": account_id,
            "symbol": symbol,
            "operation": operation,
            "order_amount": order_amount,
            "take_profit": take_profit,
            "stop_loss": stop_loss,
        }
    }