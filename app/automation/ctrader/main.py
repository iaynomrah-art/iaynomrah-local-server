from playwright.async_api import async_playwright
from app.automation.ctrader.login import login
from app.automation.ctrader.check_user import check_user
from app.automation.ctrader.place_order import place_order
from app.automation.ctrader.edit_place_order import edit_place_order
from app.automation.ctrader.input_order import input_order
import asyncio
import sys
import json

async def run(
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
    async with async_playwright() as p:
        browser = None
        page = None
        is_shared = False
        
        # Try to connect to an existing browser instance via CDP
        import httpx
        try:
            async with httpx.AsyncClient() as client:
                # Check if the remote debugging port is active
                resp = await client.get("http://127.0.0.1:9222/json/version", timeout=1.0)
                if resp.status_code == 200:
                    print("Existing browser detected. Connecting via CDP...")
                    browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
                    is_shared = True
                    # Look for an existing cTrader page
                    for context in browser.contexts:
                        for p_obj in context.pages:
                            if "app.ctrader.com" in p_obj.url:
                                page = p_obj
                                print("Existing cTrader tab found. Reusing it.")
                                try:
                                    await page.bring_to_front()
                                except:
                                    pass
                                break
                        if page: break
        except Exception:
            print("No existing browser found or connection failed.")

        if not browser:
            print("Launching new browser instance...")
            browser = await p.chromium.launch(
                channel="chrome",
                headless=False,
                args=["--remote-debugging-port=9222"]
            )
            is_shared = False

        if not page:
            if is_shared:
                print("No existing cTrader tab found in shared browser. Opening new tab.")
                # For shared browser, we need to use a context
                context = browser.contexts[0] if browser.contexts else await browser.new_context()
                page = await context.new_page()
            else:
                page = await browser.new_page()
            
            await page.goto("https://app.ctrader.com")
            # Clear initial page if it's the default blank one in a new browser
            if not is_shared:
                # Close the very first blank page if it exists
                all_pages = browser.contexts[0].pages
                if len(all_pages) > 1 and all_pages[0].url == "about:blank":
                    await all_pages[0].close()

        # Check login status more robustly
        print("Checking login status...")
        login_button_selector = 'button[type="button"]:has-text("Log in")'
        dashboard_selector = 'svg#ic_tree_expanded'
        
        try:
            # Wait for either the login button OR the dashboard to appear
            await page.wait_for_selector(
                f'{login_button_selector}, {dashboard_selector}',
                state="visible",
                timeout=20000
            )
            
            # Check which one we found
            found_login = await page.locator(login_button_selector).count() > 0
            if found_login:
                print("Not logged in. Starting login flow...")
                await login(page, username, password)
            else:
                print("Dashboard detected. Already logged in.")
        except Exception as e:
            print(f"Could not determine login status (timeout): {str(e)}")
            print("Attempting to proceed anyway...")

        # Verify the user and select the correct account
        await check_user(page, username, account_id)

        # Prepare the result (Early return for 'checkaccount' phase)
        result = {
            "status": "success",
            "message": f"cTrader account check completed for {account_id}. Order input skipped as requested.",
            "details": {
                "account_id": account_id,
                "symbol": symbol,
                "status": "account_verified"
            }
        }

        # Print the result immediately so the web server can catch it
        print(f"RESULT_JSON:{json.dumps(result)}")
        sys.stdout.flush()

        # Keep the browser open only if we are the 'launcher' process
        if is_shared:
            print("Work complete on shared browser. Closing connection (browser stays open).")
            return result
            
        print("-" * 30)
        print("LAUNCHER PROCESS: Persistence active.")
        print("The browser will remain open as long as this process is running.")
        print("-" * 30)
        
        # Wait until the browser is closed or disconnected
        try:
            while browser.is_connected():
                await asyncio.sleep(2)
        except Exception:
            pass
            
        print("Browser disconnected. Exiting process.")
        return result

        # Note: Order execution code (place_order, input_order, etc.) is currently 
        # removed/skipped to fulfill the "just checkaccount" request.
