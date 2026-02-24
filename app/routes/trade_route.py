import asyncio
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Literal
from app.automation.ctrader.main import run as run_ctrader

router = APIRouter()

class CTraderTradeRequest(BaseModel):
    username: str = Field(..., description="Username for the account")
    password: str = Field(None, description="Password for the account")
    purchase_type: Literal["buy", "sell"] = Field(None, description="Type of purchase: buy or sell")
    order_amount: str = Field(None, description="Amount to trade (e.g., '0.1')")
    take_profit: str = Field(None, description="Take profit value")
    stop_loss: str = Field(None, description="Stop loss value")
    account_id: str = Field(None, description="The trading account ID")
    symbol: str = Field(None, description="Symbol to trade (e.g., 'EURUSD')")
    operation: Literal["default", "edit-place-order", "place-order", "input-order", "execute-order"] = Field(
        "default", 
        description="The operation to perform"
    )

@router.get("/trade/credentials")
async def get_ctrader_credentials():
    """Fetch all cTrader platform credentials from Supabase."""
    from app.core.supabase import get_supabase
    
    supabase = get_supabase()
    response = supabase.table("credentials").select("*").eq("platform", "cTrader").execute()
    
    return response.data

@router.post("/trade/ctrader")
async def run_ctrader_automation(trade_data: CTraderTradeRequest):
    """
    Run cTrader automation using Playwright with validated trading parameters.
    """
    try:
        # Run the synchronous Playwright automation in a thread pool
        # so it doesn't block the async event loop
        result = await asyncio.to_thread(
            run_ctrader,
            username=trade_data.username,
            password=trade_data.password,
            purchase_type=trade_data.purchase_type,
            order_amount=trade_data.order_amount,
            take_profit=trade_data.take_profit,
            stop_loss=trade_data.stop_loss,
            account_id=trade_data.account_id,
            symbol=trade_data.symbol,
            operation=trade_data.operation,
        )

        if result.get("status") == "error":
            raise HTTPException(
                status_code=400, 
                detail=result.get("message", "Automation failed to execute")
            )

        return result

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
