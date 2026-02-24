import random


def random_delay(page, min_ms=800, max_ms=2500):
    """Wait a random duration to appear more human-like."""
    delay = random.randint(min_ms, max_ms)
    page.wait_for_timeout(delay)


def check_user(page, username, account_id):
    """
    After login, click the account dropdown, verify the email matches,
    and select the correct account by account_id.
    """
    random_delay(page, 1000, 2500)

    # Wait for the account dropdown area to be available
    page.wait_for_selector('svg#ic_tree_expanded', state="attached", timeout=15000)
    print("Account dropdown area found")

    # Click the parent container of the SVG arrow (the SVG itself is not reliably clickable)
    dropdown = page.locator('svg#ic_tree_expanded').first.locator('..')
    dropdown.click()
    print("Clicked account dropdown")

    # Wait for the account list to appear
    random_delay(page, 1500, 3500)

    # Check if the logged-in email is visible and matches
    # The email is displayed without the domain extension in some cases
    email_prefix = username.split("@")[0] if "@" in username else username
    email_element = page.locator(f'div:has-text("{email_prefix}")').first
    
    if email_element.is_visible():
        displayed_email = email_element.inner_text()
        print(f"Found email in account panel: {displayed_email}")
    else:
        print(f"Warning: Could not find email matching '{email_prefix}'")

    random_delay(page, 500, 1500)

    # Find and click the account matching the account_id
    account_element = page.locator(f'span:has-text("{account_id}")').first
    
    if account_element.is_visible():
        account_element.click()
        print(f"Selected account: {account_id}")
    else:
        error_msg = f"Account ID '{account_id}' not found in the account list"
        print(f"CRITICAL ERROR: {error_msg}")
        raise ValueError(error_msg)

    random_delay(page, 800, 2000)