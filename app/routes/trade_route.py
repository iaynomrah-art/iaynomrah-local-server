import asyncio
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Literal, Optional
from app.automation.ctrader.main import run as run_ctrader
from app.automation.tradelocker.main import run as run_tradelocker

router = APIRouter()

TradeOperation = Literal[
    "default",
    "login-only",
    "edit-place-order",
    "place-order",
    "input-order",
    "auto-place-order",
    "trade-terminator",
    "auto-place-and-terminate",
    "place-and-terminate",
    "close-position",
]

class CTraderTradeRequest(BaseModel):
    username: str = Field(..., description="Username for the account")
    password: Optional[str] = Field(None, description="Password for the account")
    purchase_type: Optional[Literal["buy", "sell"]] = Field(None, description="Type of purchase: buy or sell")
    order_amount: Optional[str] = Field(None, description="Amount to trade (e.g., '0.1')")
    take_profit: Optional[str] = Field(None, description="Take profit value")
    stop_loss: Optional[str] = Field(None, description="Stop loss value")
    account_id: Optional[str] = Field(None, description="The trading account ID")
    db_account_id: Optional[str] = Field(None, description="The unique database UUID/Hex ID of the trading account")
    symbol: Optional[str] = Field(None, description="Symbol to trade (e.g., 'EURUSD')")
    operation: TradeOperation = Field(
        "default", 
        description="The operation to perform"
    )


class TradeLockerTradeRequest(BaseModel):
    username: str = Field(..., description="Username for the account")
    password: Optional[str] = Field(None, description="Password for the account")
    server: Optional[str] = Field(None, description="TradeLocker server/broker name (e.g., HEROFX)")
    purchase_type: Optional[Literal["buy", "sell"]] = Field(None, description="Type of purchase: buy or sell")
    order_amount: Optional[str] = Field(None, description="Amount to trade (e.g., '0.1')")
    take_profit: Optional[str] = Field(None, description="Take profit value")
    stop_loss: Optional[str] = Field(None, description="Stop loss value")
    account_id: Optional[str] = Field(None, description="The trading account ID")
    db_account_id: Optional[str] = Field(None, description="The unique database UUID/Hex ID of the trading account")
    symbol: Optional[str] = Field(None, description="Symbol to trade (e.g., 'EURUSD')")
    operation: TradeOperation = Field(
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


@router.get("/trade/credentials/{platform}")
async def get_platform_credentials(platform: str):
    """Fetch all platform credentials from Supabase by platform name."""
    from app.core.supabase import get_supabase

    supabase = get_supabase()
    response = supabase.table("credentials").select("*").eq("platform", platform).execute()

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
            db_account_id=trade_data.db_account_id,
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


@router.post("/trade/tradelocker")
async def run_tradelocker_automation(trade_data: TradeLockerTradeRequest):
    """
    Run TradeLocker automation using Playwright with validated trading parameters.
    """
    try:
        result = await asyncio.to_thread(
            run_tradelocker,
            username=trade_data.username,
            password=trade_data.password,
            server=trade_data.server,
            purchase_type=trade_data.purchase_type,
            order_amount=trade_data.order_amount,
            take_profit=trade_data.take_profit,
            stop_loss=trade_data.stop_loss,
            account_id=trade_data.account_id,
            db_account_id=trade_data.db_account_id,
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
