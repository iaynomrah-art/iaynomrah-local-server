from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
from dotenv import load_dotenv, set_key

router = APIRouter()

from typing import Optional
from pydantic import BaseModel, Field

class DashboardConfig(BaseModel):
    ui_robot_path: Optional[str] = Field(None, alias="UI_ROBOT_PATH")
    publish_automation_folder: Optional[str] = Field(None, alias="PUBLISH_AUTOMATION_FOLDER")

@router.get("/dashboard/")
async def get_dashboard_config():
    """Get the current configuration from .env"""
    load_dotenv() # Reload in case of changes
    
    ui_robot_path = os.getenv("UI_ROBOT_PATH", "")
    publish_automation_folder = os.getenv("PUBLISH_AUTOMATION_FOLDER", "")
    
    return {
        "UI_ROBOT_PATH": ui_robot_path,
        "PUBLISH_AUTOMATION_FOLDER": publish_automation_folder,
        "UI_ROBOT_PATH_STATUS": "hasValue" if ui_robot_path else "empty",
        "PUBLISH_AUTOMATION_FOLDER_STATUS": "hasValue" if publish_automation_folder else "empty"
    }

@router.post("/dashboard/")
async def update_dashboard_config(config: DashboardConfig):
    """Update configuration and save to .env file"""
    env_file = ".env"
    
    # Check if .env exists
    if not os.path.exists(env_file):
        # Allow creating new env file if it doesn't exist? Or raise error?
        # Assuming it should exist based on previous context.
        pass
    
    try:
        # Update .env file
        if config.ui_robot_path is not None:
            set_key(env_file, "UI_ROBOT_PATH", config.ui_robot_path)
            
        if config.publish_automation_folder is not None:
            set_key(env_file, "PUBLISH_AUTOMATION_FOLDER", config.publish_automation_folder)
        
        # Reload environment variables for the current process
        load_dotenv(override=True)
        
        return {
            "message": "Configuration updated successfully",
            "UI_ROBOT_PATH": os.getenv("UI_ROBOT_PATH"),
            "PUBLISH_AUTOMATION_FOLDER": os.getenv("PUBLISH_AUTOMATION_FOLDER")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update .env: {str(e)}")
