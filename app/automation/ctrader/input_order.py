import random

async def random_delay(page, min_ms=800, max_ms=2500):
    """Wait a random duration to appear more human-like."""
    delay = random.randint(min_ms, max_ms)
    await page.wait_for_timeout(delay)

async def input_order(page, purchase_type, order_amount, symbol, take_profit, stop_loss):
    """
    Fills in the order form fields: symbol, purchase type (buy/sell),
    order amount, take profit, and stop loss.
    """
    print(f"Inputting order: {purchase_type} {order_amount} {symbol} TP:{take_profit} SL:{stop_loss}")

    await random_delay(page, 500, 1500)

    # Search and select the symbol
    symbol_input = page.locator('input[placeholder="Search"]').first
    if await symbol_input.is_visible():
        await symbol_input.fill(symbol)
        print(f"Searched for symbol: {symbol}")
        await random_delay(page, 1000, 2000)

        # Click the symbol from search results
        symbol_result = page.locator(f'text="{symbol}"').first
        if await symbol_result.is_visible():
            await symbol_result.click()
            print(f"Selected symbol: {symbol}")
    
    await random_delay(page, 500, 1200)

    # Select buy or sell
    if purchase_type.lower() == "buy":
        buy_button = page.locator('button:has-text("Buy")').first
        if await buy_button.is_visible():
            await buy_button.click()
            print("Selected: Buy")
    elif purchase_type.lower() == "sell":
        sell_button = page.locator('button:has-text("Sell")').first
        if await sell_button.is_visible():
            await sell_button.click()
            print("Selected: Sell")

    await random_delay(page, 400, 1000)

    # Fill in the order amount/volume
    amount_input = page.locator('input[type="text"]').nth(1)
    if await amount_input.is_visible():
        await amount_input.fill(str(order_amount))
        print(f"Entered order amount: {order_amount}")

    await random_delay(page, 400, 1000)

    # Fill in take profit
    if take_profit:
        tp_input = page.locator('input[placeholder="T/P"]').first
        if await tp_input.is_visible():
            await tp_input.fill(str(take_profit))
            print(f"Entered take profit: {take_profit}")

    await random_delay(page, 400, 1000)

    # Fill in stop loss
    if stop_loss:
        sl_input = page.locator('input[placeholder="S/L"]').first
        if await sl_input.is_visible():
            await sl_input.fill(str(stop_loss))
            print(f"Entered stop loss: {stop_loss}")

    await random_delay(page, 300, 800)
    print("Order input complete.")
