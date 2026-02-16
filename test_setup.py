
import sys
import os
from dotenv import load_dotenv

# Add current dir to path so imports work
sys.path.append(os.getcwd())

load_dotenv()

try:
    print("Testing imports...")
    from app.core.supabase import get_supabase
    from app.helper.uipath import run_uipath_automation
    print("Imports OK.")
    
    print("Initializing Supabase...")
    client = get_supabase()
    print("Supabase client initialized.")
    
    # We won't actually query because we might not have internet or valid keys yet, 
    # but initialization confirms libraries are present.
    
except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
