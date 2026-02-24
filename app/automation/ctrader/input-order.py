import random


def random_delay(page, min_ms=800, max_ms=2500):
    """Wait a random duration to appear more human-like."""
    delay = random.randint(min_ms, max_ms)
    page.wait_for_timeout(delay)


def input_order(page, purchase_type, order_amount, symbol, take_profit, stop_loss):
    """
    Fills in the order form fields: symbol, purchase type (buy/sell),
    order amount, take profit, and stop loss.
    """
    print(f"Inputting order: {purchase_type} {order_amount} {symbol} TP:{take_profit} SL:{stop_loss}")

    random_delay(page, 500, 1500)

    # Search and select the symbol
    symbol_input = page.locator('input[placeholder="Search"]').first
    if symbol_input.is_visible():
        symbol_input.fill(symbol)
        print(f"Searched for symbol: {symbol}")
        random_delay(page, 1000, 2000)

        # Click the symbol from search results
        symbol_result = page.locator(f'text="{symbol}"').first
        if symbol_result.is_visible():
            symbol_result.click()
            print(f"Selected symbol: {symbol}")
    
    random_delay(page, 500, 1200)

    # Select buy or sell
    if purchase_type.lower() == "buy":
        buy_button = page.locator('button:has-text("Buy")').first
        if buy_button.is_visible():
            buy_button.click()
            print("Selected: Buy")
    elif purchase_type.lower() == "sell":
        sell_button = page.locator('button:has-text("Sell")').first
        if sell_button.is_visible():
            sell_button.click()
            print("Selected: Sell")

    random_delay(page, 400, 1000)

    # Fill in the order amount/volume
    amount_input = page.locator('input[type="text"]').nth(1)
    if amount_input.is_visible():
        amount_input.fill(str(order_amount))
        print(f"Entered order amount: {order_amount}")

    random_delay(page, 400, 1000)

    # Fill in take profit
    if take_profit:
        tp_input = page.locator('input[placeholder="T/P"]').first
        if tp_input.is_visible():
            tp_input.fill(str(take_profit))
            print(f"Entered take profit: {take_profit}")

    random_delay(page, 400, 1000)

    # Fill in stop loss
    if stop_loss:
        sl_input = page.locator('input[placeholder="S/L"]').first
        if sl_input.is_visible():
            sl_input.fill(str(stop_loss))
            print(f"Entered stop loss: {stop_loss}")

    random_delay(page, 300, 800)
    print("Order input complete.")