import os
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')

# Initialize supabase client with service key for server-side operations
supabase: Client = None
if SUPABASE_URL and SUPABASE_SERVICE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        print(f"Supabase client initialized successfully")
    except Exception as e:
        print(f"Failed to initialize Supabase client: {e}")
        supabase = None
else:
    print(f"Missing Supabase credentials: URL={bool(SUPABASE_URL)}, SERVICE_KEY={bool(SUPABASE_SERVICE_KEY)}")

def add_user_history(user_id, action, details=None):
    try:
        # Skip history if no user_id or no supabase client
        if not user_id or not supabase:
            print(f"Skipping history: user_id={user_id}, supabase_client={bool(supabase)}")
            return None
            
        # Ensure user_id is a string
        user_id_str = str(user_id)
        
        data = {
            'user_id': user_id_str,
            'action': action,
            'details': details,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        print(f"Inserting history: {data}")
        response = supabase.table('user_history').insert(data).execute()
        print(f"History insert response: {response.data}")
        
        if response.data:
            print(f"✅ Successfully added history record for user {user_id_str}: {action}")
        else:
            print(f"⚠️ History insert returned empty data for user {user_id_str}")
            
        return response.data
    except Exception as e:
        error_msg = str(e)
        if 'violates foreign key constraint' in error_msg and 'users' in error_msg:
            print(f"❌ ERROR: Users table missing. Please run the SQL setup script first.")
            print(f"The user_id {user_id} doesn't exist in the users table.")
        elif 'Could not find the table' in error_msg:
            print(f"❌ ERROR: Required database tables are missing. Please run the SQL setup script.")
        else:
            print(f"❌ ERROR in add_user_history: {e}")
            import traceback
            print(f"Full traceback: {traceback.format_exc()}")
        return None

def get_user_history(user_id, limit=50):
    try:
        if not user_id or not supabase:
            print(f"Cannot get history: user_id={user_id}, supabase_client={bool(supabase)}")
            return []
            
        print(f"Fetching history for user: {user_id}")
        response = supabase.table('user_history').select('*').eq('user_id', user_id).order('timestamp', desc=True).limit(limit).execute()
        print(f"History fetch response: {len(response.data) if response.data else 0} records")
        return response.data
    except Exception as e:
        print(f"Supabase connection error in get_user_history: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return []

def save_generated_document(user_id, document_type, language, title, content, data=None):
    """Save a generated document to the database"""
    try:
        if not user_id or not supabase:
            print(f"Cannot save document: user_id={user_id}, supabase_client={bool(supabase)}")
            return None
            
        document_data = {
            'user_id': user_id,
            'document_type': document_type,
            'language': language,
            'title': title,
            'content': content,
            'data': data
        }
        
        print(f"Saving document: {document_type} for user {user_id}")
        response = supabase.table('generated_documents').insert(document_data).execute()
        print(f"Document save response: {response.data}")
        return response.data
    except Exception as e:
        print(f"ERROR in save_generated_document: {e}")
        return None

def get_user_documents(user_id, limit=50):
    """Get user's generated documents"""
    try:
        if not user_id or not supabase:
            print(f"Cannot get documents: user_id={user_id}, supabase_client={bool(supabase)}")
            return []
        
        # Check if generated_documents table exists
        try:
            supabase.table('generated_documents').select('id').limit(1).execute()
        except Exception as table_error:
            print(f"generated_documents table not found: {table_error}")
            return []
            
        print(f"Fetching documents for user: {user_id}")
        response = supabase.table('generated_documents').select('*').eq('user_id', user_id).order('created_at', desc=True).limit(limit).execute()
        print(f"Documents fetch response: {len(response.data) if response.data else 0} records")
        print(f"Raw documents response: {response.data}")
        return response.data
    except Exception as e:
        print(f"ERROR in get_user_documents: {e}")
        return []
