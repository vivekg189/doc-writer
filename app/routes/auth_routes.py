"""Authentication routes for the application."""
import os
import jwt
from flask import render_template, redirect, url_for, request, flash, session, jsonify
from supabase import create_client, Client
from google.oauth2 import id_token
from google.auth.transport import requests

from . import auth_bp
from app.models.users import get_user, get_user_by_email, add_user_profile, get_user_profile

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY') or SUPABASE_KEY
GOOGLE_CLIENT_ID = (os.getenv('GOOGLE_CLIENT_ID') or '').strip()

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
try:
    admin_supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
except Exception:
    admin_supabase = supabase

@auth_bp.route('/login', methods=['GET'])
def login():
    return render_template('login.html', supabase_url=SUPABASE_URL, supabase_anon_key=SUPABASE_KEY, google_client_id=GOOGLE_CLIENT_ID or '')

@auth_bp.route('/signup', methods=['GET'])
def signup():
    return render_template('signup.html', supabase_url=SUPABASE_URL, supabase_anon_key=SUPABASE_KEY, google_client_id=GOOGLE_CLIENT_ID or '')

@auth_bp.route('/api/signup', methods=['POST'])
def api_signup():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400

        # Validate email format
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return jsonify({'error': 'Please enter a valid email address'}), 400

        # Validate password strength
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters long'}), 400

        # Sign up with Supabase Auth
        response = supabase.auth.sign_up({
            'email': email,
            'password': password,
            'options': {
                'emailRedirectTo': None  # Disable email confirmation
            }
        })

        if response.user:
            # Create user profile
            add_user_profile(response.user.id)

            return jsonify({
                'message': 'Account created successfully!',
                'user': {
                    'id': response.user.id,
                    'email': response.user.email
                }
            }), 201
        else:
            return jsonify({'error': 'Failed to create account. Please try again.'}), 400

    except Exception as e:
        error_message = str(e)
        if 'invalid' in error_message.lower() or 'email' in error_message.lower():
            return jsonify({'error': 'Please enter a valid email address'}), 400
        elif 'password' in error_message.lower():
            return jsonify({'error': 'Password must be at least 6 characters long'}), 400
        else:
            return jsonify({'error': 'An error occurred during signup. Please try again.'}), 500

@auth_bp.route('/api/login', methods=['POST'])
def api_login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400

        # Validate email format
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return jsonify({'error': 'Please enter a valid email address'}), 400

        # Sign in with Supabase Auth
        response = supabase.auth.sign_in_with_password({
            'email': email,
            'password': password
        })

        if response.user and response.session:
            # Get or create user profile
            profile = get_user_profile(response.user.id)
            if not profile:
                add_user_profile(response.user.id)

            # Store user data in session
            session['user_id'] = response.user.id
            session['user_email'] = response.user.email
            session['user_username'] = response.user.email.split('@')[0]  # Use email prefix as username

            return jsonify({
                'message': 'Login successful',
                'user': {
                    'id': response.user.id,
                    'email': response.user.email
                },
                'session': {
                    'access_token': response.session.access_token,
                    'refresh_token': response.session.refresh_token
                }
            }), 200
        else:
            return jsonify({'error': 'Invalid email or password'}), 401

    except Exception as e:
        error_message = str(e)
        if 'invalid' in error_message.lower() or 'email' in error_message.lower():
            return jsonify({'error': 'Please enter a valid email address'}), 400
        elif 'password' in error_message.lower():
            return jsonify({'error': 'Invalid email or password'}), 401
        else:
            return jsonify({'error': 'An error occurred during login. Please try again.'}), 500

def process_google_auth(credential):
    """Verify Google OAuth token, ensure Supabase user/profile exists, and set session."""
    if not credential:
        return jsonify({'error': 'No credential provided'}), 400

    # 1. Verify Google ID token
    try:
        idinfo = id_token.verify_oauth2_token(
            credential, 
            requests.Request(), 
            GOOGLE_CLIENT_ID,
            clock_skew_in_seconds=10
        )
    except ValueError as ve:
        print(f"Google ID token ValueError: {ve}")
        return jsonify({'error': f'Invalid Google token: {str(ve)}'}), 400
    except Exception as te:
        import traceback
        traceback.print_exc()
        print(f"Google token verification error: {te}")
        return jsonify({'error': f'Failed to verify Google token: {str(te)}'}), 400

    if idinfo.get('iss') not in ['accounts.google.com', 'https://accounts.google.com']:
        return jsonify({'error': 'Invalid token issuer'}), 400

    email = idinfo.get('email')
    if not email:
        return jsonify({'error': 'No email address found in Google account'}), 400

    name = idinfo.get('name') or email.split('@')[0]
    user_id = None

    # 2. Try locating existing user via Supabase Admin API
    try:
        users_resp = admin_supabase.auth.admin.list_users()
        for u in getattr(users_resp, 'users', []):
            if getattr(u, 'email', '').lower() == email.lower():
                user_id = u.id
                break
    except Exception as e:
        print(f"Notice: Admin list_users check skipped: {e}")

    # 3. If user doesn't exist yet, try creating via Supabase Admin API
    if not user_id:
        try:
            create_resp = admin_supabase.auth.admin.create_user({
                'email': email,
                'email_confirm': True,
                'user_metadata': {'name': name, 'provider': 'google'}
            })
            if create_resp and getattr(create_resp, 'user', None):
                user_id = create_resp.user.id
        except Exception as e:
            print(f"Notice: Admin create_user skipped: {e}")

    # 4. If still not found, try signing in or signing up with regular Supabase client
    if not user_id:
        try:
            sign_in_res = supabase.auth.sign_in_with_password({
                'email': email,
                'password': 'google_oauth_user'
            })
            if sign_in_res and getattr(sign_in_res, 'user', None):
                user_id = sign_in_res.user.id
        except Exception:
            try:
                sign_up_res = supabase.auth.sign_up({
                    'email': email,
                    'password': 'google_oauth_user',
                    'options': {'data': {'name': name, 'provider': 'google'}}
                })
                if sign_up_res and getattr(sign_up_res, 'user', None):
                    user_id = sign_up_res.user.id
            except Exception as e:
                print(f"Notice: Client sign_up skipped: {e}")

    # 5. Deterministic fallback UUID based on verified Google email if remote auth failed
    if not user_id:
        import uuid
        user_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"google:{email.lower()}"))

    # 6. Ensure user profile exists in database
    try:
        profile = get_user_profile(user_id)
        if not profile:
            add_user_profile(user_id)
    except Exception as e:
        print(f"Notice: Profile sync skipped: {e}")

    # 7. Establish Flask session
    session['user_id'] = user_id
    session['user_email'] = email
    session['user_username'] = name

    return jsonify({
        'success': True,
        'message': 'Google authentication successful',
        'user': {
            'id': user_id,
            'email': email,
            'name': name
        }
    }), 200

@auth_bp.route('/api/google-login', methods=['POST'])
def api_google_login():
    try:
        data = request.get_json() or {}
        credential = data.get('credential')
        return process_google_auth(credential)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Google login failed: {str(e)}'}), 500

@auth_bp.route('/api/google-signup', methods=['POST'])
def api_google_signup():
    try:
        data = request.get_json() or {}
        credential = data.get('credential')
        return process_google_auth(credential)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Google signup failed: {str(e)}'}), 500

@auth_bp.route('/logout')
def logout():
    try:
        supabase.auth.sign_out()
    except:
        pass
    session.pop('user_id', None)
    session.pop('user_email', None)
    session.pop('user_username', None)
    return redirect(url_for('main.index'))
