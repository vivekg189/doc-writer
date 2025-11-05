import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')

# Initialize Supabase client with service key for server-side operations
supabase = None
if SUPABASE_URL and SUPABASE_SERVICE_KEY and SUPABASE_URL != 'your_supabase_url_here':
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    except Exception as e:
        print(f"Failed to initialize Supabase client: {e}")
        supabase = None

def get_user(user_id):
    if not supabase:
        return None
    try:
        # Get from auth user
        auth_response = supabase.auth.admin.get_user_by_id(user_id)
        if auth_response.user:
            return auth_response.user
    except Exception as e:
        print(f"Error in get_user: {e}")
    return None

def get_user_by_email(email):
    if not supabase:
        return None
    try:
        # Get user from Supabase Auth by email
        response = supabase.auth.admin.list_users()
        for user in response.users:
            if user.email == email:
                return user
    except Exception as e:
        print(f"Supabase connection error in get_user_by_email: {e}")
    return None

def add_user_profile(user_id, email=None, username=None):
    if not supabase:
        return None
    try:
        # Check if user already exists in user_profiles table
        existing_user = get_user_profile(user_id)
        if existing_user:
            return existing_user

        data = {
            'user_id': user_id,
            'language_preference': 'en'
        }
        response = supabase.table('user_profiles').insert(data).execute()
        return response.data
    except Exception as e:
        print(f"Error in add_user_profile: {e}")
        return None

def get_user_profile(user_id):
    if not supabase:
        return None
    try:
        response = supabase.table('user_profiles').select('*').eq('user_id', user_id).execute()
        if response.data:
            return response.data[0]
    except Exception as e:
        print(f"Error in get_user_profile: {e}")
    return None

def get_user_from_session(session):
    """Get user data from session."""
    if 'user_id' in session and 'user_username' in session:
        return {
            'id': session['user_id'],
            'username': session['user_username'],
            'email': session.get('user_email', '')
        }
    return None
