from app.core.supabase import get_supabase
from app.helper.system import get_machine_guid
import socket
import os
from dotenv import load_dotenv

load_dotenv()

import anyio

async def register_unit():
    """
    Registers the current machine as a unit in the database using its MachineGuid.
    Checks if it already exists before inserting.
    """
    def _sync_registration():
        guid = get_machine_guid()
        hostname = socket.gethostname()
        supabase = get_supabase()
        
        print(f"Registering unit with GUID: {guid}")
        
        try:
            # Check if unit exists
            response = supabase.table("units").select("*").eq("guid", guid).execute()
            
            unit_data = {
                "guid": guid,
                "unit_name": hostname,
                "franchise_id": os.getenv("FRANCHISE_ID"),
                "api_base_url": os.getenv("API_BASE_URL"),
                "status": "enabled"
            }
            
            if response.data:
                print(f"Unit already registered: {response.data[0]}")
                # Update existing unit to ensure api_base_url is up to date
                update_response = supabase.table("units").update(unit_data).eq("guid", guid).execute()
                if update_response.data:
                    print(f"Successfully updated unit: {update_response.data[0]}")
                    return update_response.data[0]
                return response.data[0]
            
            # Create new unit
            insert_response = supabase.table("units").insert(unit_data).execute()
            
            if insert_response.data:
                print(f"Successfully registered new unit: {insert_response.data[0]}")
                return insert_response.data[0]
                
        except Exception as e:
            print(f"Failed to register or update unit: {e}")
            return None

    # Run the blocking logic in a thread to keep the event loop responsive
    return await anyio.to_thread.run_sync(_sync_registration)
