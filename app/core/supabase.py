import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get Supabase credentials from environment variables
# We use the Service Secret Key as per your request for administrative access
supabase_url = os.getenv("PUBLIC_SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_SECRET_KEY")

if not supabase_url or not supabase_key:
    raise ValueError("PUBLIC_SUPABASE_URL and SUPABASE_SERVICE_SECRET_KEY must be set in environment variables.")

# Initialize the Supabase client
supabase: Client = create_client(supabase_url, supabase_key)

def get_supabase() -> Client:
    """
    Returns the Supabase client instance.
    """
    return supabase
