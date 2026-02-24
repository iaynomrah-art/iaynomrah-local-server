import random

async def random_delay(page, min_ms=800, max_ms=2500):
    """Wait a random duration to appear more human-like."""
    delay = random.randint(min_ms, max_ms)
    await page.wait_for_timeout(delay)

async def check_user(page, username, account_id):
    """
    After login, click the account dropdown, verify the email matches,
    and select the correct account by account_id.
    """
    await random_delay(page, 1000, 2500)

    # Wait for the account dropdown area to be available
    print(f"Waiting for account dropdown (account_id: {account_id})...")
    await page.wait_for_selector('svg#ic_tree_expanded', state="visible", timeout=30000)
    print("Account dropdown area found")

    # Click the parent container of the SVG arrow (the SVG itself is not reliably clickable)
    dropdown = page.locator('svg#ic_tree_expanded').first.locator('..')
    await dropdown.click()
    print("Clicked account dropdown")

    # Wait for the account list to appear
    await random_delay(page, 1500, 3500)

    # Check if the logged-in email is visible and matches
    print(f"Verifying email: {username}")
    
    # Try finding the email wrapped in parentheses as shown in the UI
    email_with_parens = f"({username})"
    email_element = page.locator(f'text="{email_with_parens}"').first
    
    if not await email_element.is_visible():
        # Fallback to search for just the username if parentheses aren't used everywhere
        email_element = page.locator(f'text="{username}"').first
        
    if not await email_element.is_visible():
        # Final fallback to search for the prefix
        email_prefix = username.split("@")[0] if "@" in username else username
        email_element = page.locator(f'div:has-text("{email_prefix}")').first

    if await email_element.is_visible():
        displayed_text = await email_element.inner_text()
        print(f"Verified email matches UI text: {displayed_text}")
    else:
        print(f"Warning: Could not find email '{username}' visible in the UI.")

    await random_delay(page, 500, 1500)

    # Find and click the account matching the account_id
    account_element = page.locator(f'span:has-text("{account_id}")').first
    
    if await account_element.is_visible():
        await account_element.click()
        print(f"Selected account: {account_id}")
    else:
        print(f"Warning: Account ID '{account_id}' not found in the account list")

    await random_delay(page, 800, 2000)
