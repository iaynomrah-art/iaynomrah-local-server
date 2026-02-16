from fastapi import APIRouter, Body, UploadFile, File, Form
from typing import List, Dict, Any, Optional
from app.controller.automation_controller import (
    Automation, 
    AutomationCreate, 
    RunResponse,
    get_all_automations,
    create_new_automation,
    get_automation_by_id,
    run_automation_process
)

router = APIRouter()

@router.get("/automation", response_model=List[Automation])
async def list_automations():
    """List all automations from Supabase."""
    return await get_all_automations()

@router.post("/automation", response_model=Automation)
async def create_automation(
    file: UploadFile = File(...),
    version: Optional[str] = Form(None)
):
    """
    Create a new automation entry in Supabase.
    Uploads the file to PUBLISH_AUTOMATION_FOLDER and saves metadata to DB.
    """
    return await create_new_automation(file=file, version=version)

@router.get("/automation/{automation_id}", response_model=Automation)
async def get_automation(automation_id: str):
    """Get a specific automation by ID."""
    return await get_automation_by_id(automation_id)

@router.post("/automation/{automation_id}/run", response_model=RunResponse)
async def run_automation(
    automation_id: str, 
    arguments: Dict[str, Any] = Body(default={})
):
    """
    Run a specific automation using UiPath. 
    Pass JSON body as arguments for the process.
    """
    return await run_automation_process(automation_id, arguments)
