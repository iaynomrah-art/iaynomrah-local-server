from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Literal
from app.controller.automation_controller import (
    get_latest_automation_by_name, 
    run_automation_process, 
    RunResponse
)

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
    Finds the latest version of 'CTraderAutomation' and runs it with validated trading parameters.
    """
    automation_name = "CTraderAutomation"
    
    # 1. Find the latest version
    latest_item = await get_latest_automation_by_name(automation_name)
    
    if not latest_item:
        raise HTTPException(
            status_code=404, 
            detail=f"No automation found for '{automation_name}'"
        )
    
    automation_id = latest_item.get("id")
    file_name = latest_item.get("file_name")
    version = latest_item.get("version", "unknown")
    
    print(f"Running latest automation: {file_name} (Version: {version}, ID: {automation_id})")

    # 2. Convert Pydantic model to dict for the robot arguments
    arguments = trade_data.model_dump()
    
    try:
        # 3. Run the automation using its specific ID
        result = await run_automation_process(automation_id, arguments)
        
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
