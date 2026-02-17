from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Literal
from app.controller.automation_controller import run_automation_by_identifier, RunResponse

router = APIRouter()

class CTraderTradeRequest(BaseModel):
    account_id: str = Field(..., description="The trading account ID")
    password: str = Field(..., description="Password for the account")
    username: str = Field(..., description="Username for the account")
    order_amount: str = Field(..., description="Amount to trade (e.g., '0.1')")
    purchase_type: Literal["buy", "sell"] = Field(..., description="Type of purchase: buy or sell")
    symbol: str = Field(..., description="Symbol to trade (e.g., 'EURUSD')")
    stop_loss: str = Field(..., description="Stop loss value")
    take_profit: str = Field(..., description="Take profit value")
    operation: Literal["default", "edit-place-order", "place-order"] = Field(
        "default", 
        description="The operation to perform"
    )

@router.post("/trade/ctrader", response_model=RunResponse)
async def run_ctrader_automation(trade_data: CTraderTradeRequest):
    """
    Specifically runs the 'CtraderAutomation' with validated trading parameters.
    """
    automation_identifier = "CtraderAutomation" # The name of your .nupkg file
    
    # Convert Pydantic model to dict for the robot arguments
    arguments = trade_data.model_dump()
    
    try:
        # We reuse the controller logic to find the record and run it
        result = await run_automation_by_identifier(automation_identifier, arguments)
        
        if result.get("status") == "error":
            raise HTTPException(
                status_code=400, 
                detail=result.get("message", "Automation failed to execute")
            )
            
        return result
        
    except HTTPException as e:
        # Re-raise explicit HTTP exceptions (like 404 if file not found)
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
