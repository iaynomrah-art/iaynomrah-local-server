import importlib

input_order_module = importlib.import_module("app.automation.tradelocker.input-order")
input_order = input_order_module.input_order

place_order_module = importlib.import_module("app.automation.tradelocker.place-order")
place_order = place_order_module.place_order


def edit_place_order(page, purchase_type, order_amount, symbol, take_profit, stop_loss):
    """
    TradeLocker fallback implementation: update order fields and submit.
    """
    fill_result = input_order(page, purchase_type, order_amount, symbol, take_profit, stop_loss)

    if isinstance(fill_result, dict):
        if not fill_result.get("success", False):
            return fill_result
    elif not fill_result:
        return {"success": False, "reason": "Failed to edit order inputs", "warning": None}

    return place_order(page)
