import asyncio
import os
import subprocess
import json
import sys
import threading
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Literal

router = APIRouter()

class CTraderTradeRequest(BaseModel):
    username: str = Field(..., description="Username for the account")
    password: str = Field(..., description="Password for the account")
    purchase_type: Literal["buy", "sell"] = Field(..., description="Type of purchase: buy or sell")
    order_amount: str = Field(..., description="Amount to trade (e.g., '0.1')")
    take_profit: str = Field(..., description="Take profit value")
    stop_loss: str = Field(..., description="Stop loss value")
    account_id: str = Field(..., description="The trading account ID")
    symbol: str = Field(..., description="Symbol to trade (e.g., 'EURUSD')")
    operation: Literal["default", "edit-place-order", "place-order"] = Field(
        "default", 
        description="The operation to perform"
    )

@router.post("/trade/ctrader")
async def run_ctrader_automation(trade_data: CTraderTradeRequest):
    """
    Run cTrader automation in a separate process to avoid asyncio loop conflicts on Windows.
    """
    try:
        # Prepare arguments for the CLI script
        args_dict = trade_data.model_dump()
        args_json = json.dumps(args_dict)
        
        # Path to the CLI script
        cli_script = os.path.join(os.path.dirname(__file__), "..", "automation", "ctrader", "cli.py")
        
        # Determine the python executable
        python_exe = sys.executable
        
        print(f"Executing automation in separate process (Threaded Popen): {cli_script}")
        
        # Use subprocess.Popen which doesn't require ProactorEventLoop
        process = subprocess.Popen(
            [python_exe, cli_script, args_json],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, # Merge stderr into stdout for easier reading
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        result_container = {"data": None, "error": None}
        result_ready = asyncio.Event()
        loop = asyncio.get_running_loop()

        def read_output():
            try:
                for line in iter(process.stdout.readline, ""):
                    stripped_line = line.strip()
                    if stripped_line:
                        print(f"Automation: {stripped_line}")
                    
                    if stripped_line.startswith("RESULT_JSON:"):
                        json_str = stripped_line.replace("RESULT_JSON:", "", 1)
                        try:
                            result_container["data"] = json.loads(json_str)
                            # Signal that we have a result safely to the main loop
                            loop.call_soon_threadsafe(result_ready.set)
                        except Exception as e:
                            print(f"Failed to parse result JSON: {e}")
            except Exception as e:
                print(f"Error in read_output thread: {e}")
                result_container["error"] = str(e)
                loop.call_soon_threadsafe(result_ready.set)
            finally:
                process.stdout.close()

        # Start output reader in a background thread
        thread = threading.Thread(target=read_output, daemon=True)
        thread.start()
        
        # Wait for either the result to be ready or the process to exit
        timeout = 180
        try:
            await asyncio.wait_for(result_ready.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            raise HTTPException(status_code=500, detail="Automation timed out (180s)")

        if result_container["data"]:
            result = result_container["data"]
            if result.get("status") == "error":
                raise HTTPException(
                    status_code=400, 
                    detail=result.get("message", "Automation failed to execute")
                )
            return result
        
        if result_container["error"]:
            raise HTTPException(status_code=500, detail=f"Reader error: {result_container['error']}")
            
        raise HTTPException(status_code=500, detail="Automation ended without producing a result")

    except HTTPException as e:
        raise e
    except Exception as e:
        error_msg = str(e) or repr(e)
        print(f"Error in run_ctrader_automation: {error_msg}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {error_msg}")
