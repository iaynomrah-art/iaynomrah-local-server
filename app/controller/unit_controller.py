from app.core.supabase import get_supabase
from app.helper.system import get_machine_guid
import socket
import os
from dotenv import load_dotenv

load_dotenv()

async def register_unit():
    """
    Registers the current machine as a unit in the database using its MachineGuid.
    Checks if it already exists before inserting.
    """
    guid = get_machine_guid()
    hostname = socket.gethostname()
    supabase = get_supabase()
    
    print(f"Registering unit with GUID: {guid}")
    
    try:
        # Check if unit exists
        response = supabase.table("units").select("*").eq("guid", guid).execute()
        
        if response.data:
            print(f"Unit already registered: {response.data[0]}")
            return response.data[0]
        
        # Create new unit
        new_unit = {
            "guid": guid,
            "franchise_id": os.getenv("FRANCHISE_ID"),
            "api_base_url": os.getenv("API_BASE_URL")
        }
        
        insert_response = supabase.table("units").insert(new_unit).execute()
        
        if insert_response.data:
            print(f"Successfully registered new unit: {insert_response.data[0]}")
            return insert_response.data[0]
            
    except Exception as e:
        print(f"Failed to register unit: {e}")
        # Make sure we don't crash the server startup, but log the error
        return None
