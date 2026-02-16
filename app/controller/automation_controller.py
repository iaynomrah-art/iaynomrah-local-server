from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import os
import re
import aiofiles
from dotenv import load_dotenv
from fastapi import UploadFile, HTTPException
from app.core.supabase import get_supabase
from app.helper.uipath import run_uipath_automation

# --- Pydantic Models based on Supabase table ---
class AutomationBase(BaseModel):
    file_name: Optional[str] = None
    version: Optional[str] = None

class AutomationCreate(AutomationBase):
    pass

class Automation(AutomationBase):
    id: str
    created_at: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class RunResponse(BaseModel):
    status: str
    message: Optional[str] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    exit_code: Optional[int] = None

# --- Controller Functions ---

async def get_all_automations():
    supabase = get_supabase()
    response = supabase.table("automations").select("*").execute()
    return response.data



async def create_new_automation(
    file: UploadFile,
    version: Optional[str] = None
):
    load_dotenv()
    publish_folder = os.getenv("PUBLISH_AUTOMATION_FOLDER")
    
    if not publish_folder:
        raise HTTPException(status_code=500, detail="PUBLISH_AUTOMATION_FOLDER is not configured")

    if not os.path.exists(publish_folder):
        os.makedirs(publish_folder)

    if not file.filename.endswith(".nupkg"):
        raise HTTPException(status_code=400, detail="Only .nupkg files are allowed")

    # Extract version if not provided
    if version is None:
        # Regex to find version pattern like .1.0.5.nupkg at the end
        match = re.search(r"\.(\d+\.\d+\.\d+(?:-[\w\.]*)?)\.nupkg$", file.filename)
        if match:
            version = match.group(1)

    # 1. Save the file locally
    file_location = os.path.join(publish_folder, file.filename)
    
    # Save locally
    async with aiofiles.open(file_location, 'wb') as out_file:
        while content := await file.read(1024 * 1024):  # Read in 1MB chunks
            await out_file.write(content)
            
    # 2. Upload to Supabase Storage if not exists
    supabase = get_supabase()
    bucket_name = "automation"
    
    # Check if file exists in bucket
    try:
        # List files in bucket matching the filename
        files_in_bucket = supabase.storage.from_(bucket_name).list(
            path=None, 
            options={"limit": 1, "search": file.filename}
        )
        file_exists_in_bucket = any(f['name'] == file.filename for f in files_in_bucket)
    except Exception as e:
        print(f"Error checking storage: {e}")
        file_exists_in_bucket = False

    if not file_exists_in_bucket:
        try:
            with open(file_location, "rb") as f:
                file_content = f.read()
                supabase.storage.from_(bucket_name).upload(
                    path=file.filename,
                    file=file_content,
                    file_options={"content-type": "application/octet-stream"}
                )
        except Exception as e:
            print(f"Failed to upload to Supabase Storage: {e}")
            # We don't raise error here, as local save was successful
            pass

    # 3. Insert record into Supabase tables
    
    # Data to insert
    data = {
        "file_name": file.filename,  # Storing absolute path might be better, or just filename if we always join with PUBLISH_AUTOMATION_FOLDER
        "version": version
    }
    
    # Clean up None values if any
    if version is None:
        del data["version"]
        
    response = supabase.table("automations").insert(data).execute()
    
    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to create automation")
    
    return response.data[0]

async def get_automation_by_id(automation_id: str):
    supabase = get_supabase()
    response = supabase.table("automations").select("*").eq("id", automation_id).execute()
    
    if not response.data:
        raise HTTPException(status_code=404, detail="Automation not found")
    
    return response.data[0]

async def run_automation_process(automation_id: str, arguments: Dict[str, Any]):
    supabase = get_supabase()
    
    # 1. Fetch automation details
    response = supabase.table("automations").select("*").eq("id", automation_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Automation not found")
    
    automation_data = response.data[0]
    file_name = automation_data.get("file_name")
    
    if not file_name:
        raise HTTPException(status_code=400, detail="Automation record has no 'file_name'")

    # Run the automation
    result = await run_uipath_automation(
        process_name_or_path=file_name,
        arguments=arguments,
        is_file=True 
    )
    
    # 3. Save to automation_history
    try:
        supabase.table("automation_history").insert({
            "automation_id": automation_id,
            "input": arguments,
            "status": result.get("status", "unknown")
        }).execute()
    except Exception as e:
        print(f"Failed to save to automation_history: {e}")
    
    return result

async def run_automation_by_identifier(identifier: str, arguments: Dict[str, Any]):
    """
    Run an automation identified by either its ID (UUID) or its file_name.
    """
    supabase = get_supabase()
    
    # Try searching by ID first (if it looks like a UUID-ish string)
    # Most common UUID pattern or if it's purely numeric (depending on DB schema)
    # Here we just try to find by ID first, then by filename if not found.
    
    automation_data = None
    
    # Try ID search
    try:
        response = supabase.table("automations").select("*").eq("id", identifier).execute()
        if response.data:
            automation_data = response.data[0]
    except Exception:
        # If it fails (e.g. invalid UUID format if ID is UUID), we'll try filename
        pass
        
    # If not found by ID, try file_name search
    if not automation_data:
        response = supabase.table("automations").select("*").eq("file_name", identifier).execute()
        if response.data:
            automation_data = response.data[0]
            
    if not automation_data:
        # Try searching with .nupkg suffix if it's missing
        if not identifier.endswith(".nupkg"):
            response = supabase.table("automations").select("*").eq("file_name", f"{identifier}.nupkg").execute()
            if response.data:
                automation_data = response.data[0]

    if not automation_data:
        raise HTTPException(status_code=404, detail=f"Automation with identifier '{identifier}' not found")
    
    file_name = automation_data.get("file_name")
    automation_id = automation_data.get("id")
    
    if not file_name:
        raise HTTPException(status_code=400, detail="Automation record has no 'file_name'")

    # Run the automation
    result = await run_uipath_automation(
        process_name_or_path=file_name,
        arguments=arguments,
        is_file=True 
    )

    # Save to automation_history
    try:
        supabase.table("automation_history").insert({
            "automation_id": automation_id,
            "input": arguments,
            "status": result.get("status", "unknown")
        }).execute()
    except Exception as e:
        print(f"Failed to save to automation_history: {e}")
    
    return result
