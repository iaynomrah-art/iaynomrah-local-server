import random
import re

async def random_delay(page, min_ms=800, max_ms=2500):
    """Wait a random duration to appear more human-like."""
    delay = random.randint(min_ms, max_ms)
    await page.wait_for_timeout(delay)

async def input_order(page, purchase_type, order_amount, symbol, take_profit, stop_loss):
    """
    Fills in the order form fields: symbol, purchase type (buy/sell),
    order amount, take profit, and stop loss.
    """
    print(f"Changing symbol to: {symbol}")

    await random_delay(page, 500, 1500)

    # Search and select the symbol
    # First, check if the search input is already visible
    symbol_input = page.locator('input[placeholder="Search"]').first
    
    if not await symbol_input.is_visible():
        # If not, it might be in a dropdown that needs to be clicked
        print("Symbol search not visible, attempting to click symbol dropdown...")
        
        # Look for the element displaying the current symbol (e.g., XAUUSD, EUR/USD)
        # According to the UI structure, it's often a div with specific pattern
        symbol_trigger = page.locator('div[tabindex="-1"]').filter(has_text=re.compile(r"^[A-Z/]{3,10}$")).first
        if not await symbol_trigger.is_visible():
             # Fallback: look for any div containing a symbol-like pattern
             symbol_trigger = page.get_by_text(re.compile(r"^[A-Z/]{3,10}$")).first
        
        if await symbol_trigger.is_visible():
            await symbol_trigger.click()
            await random_delay(page, 800, 1500)
            symbol_input = page.locator('input[placeholder="Search"]').first

    if await symbol_input.is_visible():
        await symbol_input.fill("") # Clear it just in case
        await symbol_input.fill(symbol)
        print(f"Searched for symbol: {symbol}")
        await random_delay(page, 1000, 2000)

        # Click the symbol from search results
        # We look for the exact symbol name in the results list
        symbol_result = page.locator(f'div:has-text("{symbol}")').filter(has_text=re.compile(f"^{symbol}$")).first
        if not await symbol_result.is_visible():
            symbol_result = page.locator(f'text="{symbol}"').first
            
        if await symbol_result.is_visible():
            await symbol_result.click()
            print(f"Selected symbol: {symbol}")
    
    await random_delay(page, 300, 800)
    print("Symbol change complete.")
