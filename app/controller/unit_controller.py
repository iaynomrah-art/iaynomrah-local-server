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
    Also checks if the local PUBLISH_AUTOMATION_FOLDER contains files from the Supabase bucket.
    """
    def _sync_registration():
        guid = get_machine_guid()
        hostname = socket.gethostname()
        supabase = get_supabase()
        
        print(f"Registering unit with GUID: {guid}")

        # Check for automations in PUBLISH_AUTOMATION_FOLDER
        publish_folder = os.getenv("PUBLISH_AUTOMATION_FOLDER")
        if publish_folder:
            # Strip path of any surrounding quotes
            publish_folder = publish_folder.strip("'").strip('"')
            
            if not os.path.exists(publish_folder):
                os.makedirs(publish_folder)
            
            try:
                local_files = os.listdir(publish_folder)
                
                # Check bucket named "automations" as requested
                bucket_name = "automations"
                bucket_files = supabase.storage.from_(bucket_name).list()
                
                # Fallback if "automations" is not found but "automation" is common in the codebase
                if not bucket_files:
                    bucket_name = "automation"
                    bucket_files = supabase.storage.from_(bucket_name).list()

                print(f"Checking for files in Supabase bucket '{bucket_name}'...")
                for b_file in bucket_files:
                    file_name = b_file.get('name')
                    if not file_name or file_name == '.emptyFolderPlaceholder':
                        continue
                    
                    if file_name not in local_files:
                        print(f"  [MISSING] {file_name} is in bucket but not in local folder. Downloading...")
                        try:
                            local_path = os.path.join(publish_folder, file_name)
                            with open(local_path, "wb") as f:
                                # Download from Supabase
                                res_download = supabase.storage.from_(bucket_name).download(file_name)
                                f.write(res_download)
                            print(f"  [DOWNLOADED] {file_name} to {local_path}")
                        except Exception as dl_err:
                            print(f"  [ERROR] Failed to download {file_name}: {dl_err}")
                    else:
                        print(f"  [FOUND] {file_name} is present locally")
            except Exception as e:
                print(f"Failed to check local or remote storage: {e}")
        else:
            print("PUBLISH_AUTOMATION_FOLDER environment variable not set.")
        
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
                "api_base_url": os.getenv("API_BASE_URL"),
                "status" : "enabled"
            }
            
            insert_response = supabase.table("units").insert(new_unit).execute()
            
            if insert_response.data:
                print(f"Successfully registered new unit: {insert_response.data[0]}")
                return insert_response.data[0]
                
        except Exception as e:
            print(f"Failed to register unit: {e}")
            return None

    # Run the blocking logic in a thread to keep the event loop responsive
    return await anyio.to_thread.run_sync(_sync_registration)
