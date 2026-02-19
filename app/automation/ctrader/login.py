import random


def random_delay(page, min_ms=800, max_ms=2500):
    """Wait a random duration to appear more human-like."""
    delay = random.randint(min_ms, max_ms)
    page.wait_for_timeout(delay)


def login(page, username, password):
    print("Opened app.ctrader.com")

    random_delay(page, 500, 1500)

    # Click the first "Log in" button
    page.click('button[type="button"]:has-text("Log in")')
    print("Clicked Log in button")

    # Wait for the login/signup panel tabs to appear
    page.wait_for_selector('[data-smoke-id="signup-tab"]', state="visible", timeout=10000)
    print("Login/Signup panel visible")

    random_delay(page, 400, 1200)

    # Check if we're on Sign Up tab; if so, click the Log in tab
    signup_tab = page.locator('[data-smoke-id="signup-tab"]')
    login_tab = signup_tab.locator('xpath=preceding-sibling::div[1]')

    # Click the "Log in" tab to make sure we're on the login form
    login_tab.click()
    print("Clicked 'Log in' tab")

    # Wait for the email input to appear after switching tabs
    page.wait_for_selector('input[placeholder="Enter email or username"]', state="visible", timeout=10000)

    random_delay(page, 500, 1500)

    # Type username
    page.fill('input[placeholder="Enter email or username"]', username)
    print("Entered username")

    random_delay(page, 600, 1800)

    # Type password
    page.fill('input[placeholder="Enter password"]', password)
    print("Entered password")

    random_delay(page, 400, 1000)

    # Click the submit "Log in" button
    page.click('button[type="submit"]:has-text("Log in")')
    print("Clicked submit")

    # Check for errors
    try:
        error = page.wait_for_selector(
            'text=/invalid|incorrect|error|wrong|failed/i',
            timeout=5000
        )
        if error:
            print(f"Login error: {error.inner_text()}")
    except:
        print("No error detected — login likely successful!")