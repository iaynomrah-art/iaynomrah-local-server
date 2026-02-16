from fastapi import APIRouter, Request, HTTPException
from typing import Dict, Any, Optional
import logging
from app.controller.automation_controller import RunResponse, run_automation_by_identifier

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/runner/{identifier}", response_model=RunResponse)
async def run_automation_by_identifier_path(
    request: Request,
    identifier: str
):
    """
    Run an automation by its ID or filename provided in the URL path.
    The 'arguments' from the request body are used if present, otherwise the entire body is used.
    """
    # Capture the entire JSON body
    try:
        body = await request.json()
    except Exception:
        body = {}

    # Logic: if body has an 'arguments' key, extract its contents (the sample payload).
    # Otherwise, use the whole body as arguments.
    automation_args = body.get("arguments", body) if isinstance(body, dict) else body
    
    # If automation_args is not a dict (e.g. empty or malicious), default to empty dict
    if not isinstance(automation_args, dict):
        automation_args = {}

    logger.info(f"Running automation via runner path: {identifier}")
    
    # Execute automation using controller
    result = await run_automation_by_identifier(identifier, automation_args)
    
    # Check if there was an error and raise HTTPException to match requested logic
    if result.get("status") == "error":
        msg = result.get("message", "Unknown error")
        status_code = 404 if "not found" in msg.lower() else 400
        raise HTTPException(status_code=status_code, detail=msg)
    
    return result

@router.get("/runner/{identifier}", response_model=RunResponse)
async def run_automation_by_identifier_get(identifier: str):
    """
    Run an automation by its ID or filename via GET (no arguments).
    """
    result = await run_automation_by_identifier(identifier, {})
    
    if result.get("status") == "error":
        msg = result.get("message", "Unknown error")
        status_code = 404 if "not found" in msg.lower() else 400
        raise HTTPException(status_code=status_code, detail=msg)
        
    return result
