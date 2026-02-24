import random

async def random_delay(page, min_ms=800, max_ms=2500):
    """Wait a random duration to appear more human-like."""
    delay = random.randint(min_ms, max_ms)
    await page.wait_for_timeout(delay)

async def login(page, username, password):
    print("Opened app.ctrader.com")

    await random_delay(page, 500, 1500)

    # Click the first "Log in" button
    await page.click('button[type="button"]:has-text("Log in")')
    print("Clicked Log in button")

    # Wait for the login/signup panel tabs to appear
    await page.wait_for_selector('[data-smoke-id="signup-tab"]', state="visible", timeout=10000)
    print("Login/Signup panel visible")

    await random_delay(page, 400, 1200)

    # Check if we're on Sign Up tab; if so, click the Log in tab
    signup_tab = page.locator('[data-smoke-id="signup-tab"]')
    login_tab = signup_tab.locator('xpath=preceding-sibling::div[1]')

    # Click the "Log in" tab to make sure we're on the login form
    await login_tab.click()
    print("Clicked 'Log in' tab")

    # Wait for the email input to appear after switching tabs
    await page.wait_for_selector('input[placeholder="Enter email or username"]', state="visible", timeout=10000)

    await random_delay(page, 500, 1500)

    # Type username
    await page.fill('input[placeholder="Enter email or username"]', username)
    print("Entered username")

    await random_delay(page, 600, 1800)

    # Type password
    await page.fill('input[placeholder="Enter password"]', password)
    print("Entered password")

    await random_delay(page, 400, 1000)

    # Click the submit "Log in" button
    await page.click('button[type="submit"]:has-text("Log in")')
    print("Clicked submit")

    # Check for errors
    try:
        error = await page.wait_for_selector(
            'text=/invalid|incorrect|error|wrong|failed/i',
            timeout=5000
        )
        if error:
            print(f"Login error: {await error.inner_text()}")
    except:
        print("No error detected — login likely successful!")

    # Wait for the main dashboard to load after login
    print("Waiting for dashboard to load...")
    try:
        await page.wait_for_selector('svg#ic_tree_expanded', state="visible", timeout=30000)
        print("Dashboard loaded successfully.")
    except Exception:
        print("Warning: Dashboard didn't appear after login attempt. It might be taking longer or failed.")