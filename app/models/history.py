import os
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def add_user_history(user_id, action, details=None):
    try:
        print(f"DEBUG: Attempting to add history - user_id: {user_id}, action: {action}, details: {details}")
        
        # Use UUID string directly - don't convert to integer
        data = {
            'user_id': user_id,
            'action': action,
            'details': details,
            'timestamp': datetime.utcnow().isoformat()
        }
        print(f"DEBUG: Data to insert: {data}")
        
        response = supabase.table('user_history').insert(data).execute()
        print(f"DEBUG: Insert response: {response}")
        return response.data
    except Exception as e:
        print(f"ERROR in add_user_history: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return None

def get_user_history(user_id, limit=50):
    try:
        # Use UUID string directly - don't convert to integer
        response = supabase.table('user_history').select('*').eq('user_id', user_id).order('timestamp', desc=True).limit(limit).execute()
        return response.data
    except Exception as e:
        print(f"Supabase connection error in get_user_history: {e}")
        return []
