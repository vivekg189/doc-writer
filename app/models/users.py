import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_user(user_id):
    try:
        # Get user from Supabase Auth
        response = supabase.auth.admin.get_user_by_id(user_id)
        if response.user:
            return response.user
    except Exception as e:
        print(f"Supabase connection error in get_user: {e}")
    return None

def get_user_by_email(email):
    try:
        # Get user from Supabase Auth by email
        response = supabase.auth.admin.list_users()
        for user in response.users:
            if user.email == email:
                return user
    except Exception as e:
        print(f"Supabase connection error in get_user_by_email: {e}")
    return None

def add_user_profile(user_id, language_preference='en'):
    try:
        # First check if user profile already exists
        existing_profile = get_user_profile(user_id)
        if existing_profile:
            return existing_profile

        data = {
            'id': user_id,
            'language_preference': language_preference
        }
        # Update users table with profile information
        response = supabase.table('users').upsert(data).execute()
        return response.data
    except Exception as e:
        print(f"Supabase connection error in add_user_profile: {e}")
        return None

def get_user_profile(user_id):
    try:
        response = supabase.table('users').select('*').eq('id', user_id).execute()
        if response.data:
            return response.data[0]
    except Exception as e:
        print(f"Supabase connection error in get_user_profile: {e}")
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
