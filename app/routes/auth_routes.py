"""Authentication routes for the application."""
import os
import jwt
from flask import render_template, redirect, url_for, request, flash, session, jsonify
from supabase import create_client, Client
from google.oauth2 import id_token
from google.auth.transport import requests

from . import auth_bp
from app.models.users import get_user, get_user_by_email, add_user_profile, get_user_profile
from app.models.history import add_user_history

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')  # Use service role key for server-side operations
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

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
            add_user_profile(response.user.id, response.user.email, response.user.email.split('@')[0])

            # Log signup activity
            print(f"DEBUG: About to log signup history for user {response.user.id}")
            history_result = add_user_history(response.user.id, 'signup', f'New account created with email: {response.user.email}')
            print(f"DEBUG: Signup history result: {history_result}")

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
                add_user_profile(response.user.id, response.user.email, response.user.email.split('@')[0])

            # Store user data in session
            session['user_id'] = response.user.id
            session['user_email'] = response.user.email
            session['user_username'] = response.user.email.split('@')[0]  # Use email prefix as username

            # Log login activity
            print(f"DEBUG: About to log login history for user {response.user.id}")
            history_result = add_user_history(response.user.id, 'login', f'User logged in with email: {response.user.email}')
            print(f"DEBUG: Login history result: {history_result}")

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

@auth_bp.route('/api/google-login', methods=['POST'])
def api_google_login():
    try:
        data = request.get_json()
        credential = data.get('credential')
        
        if not credential:
            return jsonify({'error': 'No credential provided'}), 400
        
        # Verify the Google ID token
        idinfo = id_token.verify_oauth2_token(
            credential, requests.Request(), GOOGLE_CLIENT_ID)
        
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            return jsonify({'error': 'Invalid token issuer'}), 400
        
        email = idinfo['email']
        name = idinfo.get('name', '')
        
        # Check if user exists in Supabase
        try:
            response = supabase.auth.sign_in_with_password({
                'email': email,
                'password': 'google_oauth_user'  # Placeholder password
            })
        except:
            # User doesn't exist, create account
            response = supabase.auth.sign_up({
                'email': email,
                'password': 'google_oauth_user',
                'options': {
                    'data': {
                        'name': name,
                        'provider': 'google'
                    }
                }
            })
        
        if response.user:
            # Get or create user profile
            profile = get_user_profile(response.user.id)
            if not profile:
                add_user_profile(response.user.id, response.user.email, name or response.user.email.split('@')[0])
            
            # Store user data in session
            session['user_id'] = response.user.id
            session['user_email'] = response.user.email
            session['user_username'] = name or response.user.email.split('@')[0]
            
            # Log Google login activity
            print(f"DEBUG: About to log Google login history for user {response.user.id}")
            history_result = add_user_history(response.user.id, 'login', f'User logged in with Google: {response.user.email}')
            print(f"DEBUG: Google login history result: {history_result}")
            
            return jsonify({
                'success': True,
                'message': 'Google login successful',
                'user': {
                    'id': response.user.id,
                    'email': response.user.email,
                    'name': name
                }
            }), 200
        else:
            return jsonify({'error': 'Failed to authenticate with Google'}), 400
            
    except ValueError as e:
        return jsonify({'error': 'Invalid Google token'}), 400
    except Exception as e:
        return jsonify({'error': 'Google login failed'}), 500

@auth_bp.route('/api/google-signup', methods=['POST'])
def api_google_signup():
    try:
        data = request.get_json()
        credential = data.get('credential')
        
        if not credential:
            return jsonify({'error': 'No credential provided'}), 400
        
        # Verify the Google ID token
        idinfo = id_token.verify_oauth2_token(
            credential, requests.Request(), GOOGLE_CLIENT_ID)
        
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            return jsonify({'error': 'Invalid token issuer'}), 400
        
        email = idinfo['email']
        name = idinfo.get('name', '')
        
        # Create new user account
        response = supabase.auth.sign_up({
            'email': email,
            'password': 'google_oauth_user',
            'options': {
                'data': {
                    'name': name,
                    'provider': 'google'
                }
            }
        })
        
        if response.user:
            # Create user profile
            add_user_profile(response.user.id, response.user.email, name or response.user.email.split('@')[0])
            
            # Store user data in session
            session['user_id'] = response.user.id
            session['user_email'] = response.user.email
            session['user_username'] = name or response.user.email.split('@')[0]
            
            # Log Google signup activity
            print(f"DEBUG: About to log Google signup history for user {response.user.id}")
            history_result = add_user_history(response.user.id, 'signup', f'New account created with Google: {response.user.email}')
            print(f"DEBUG: Google signup history result: {history_result}")
            
            return jsonify({
                'success': True,
                'message': 'Google signup successful',
                'user': {
                    'id': response.user.id,
                    'email': response.user.email,
                    'name': name
                }
            }), 201
        else:
            return jsonify({'error': 'Failed to create account with Google'}), 400
            
    except ValueError as e:
        return jsonify({'error': 'Invalid Google token'}), 400
    except Exception as e:
        return jsonify({'error': 'Google signup failed'}), 500

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
