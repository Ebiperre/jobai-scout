
from supabase import create_client, Client
from dotenv import load_dotenv
import os

load_dotenv()
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

print("URL:", supabase_url)
print("Key:", supabase_key)

try:
    supabase: Client = create_client(supabase_url, supabase_key)
    response = supabase.table("jobs").select("*").limit(1).execute()
    print("Test query response:", response.data)
except Exception as e:
    print("Error:", str(e))