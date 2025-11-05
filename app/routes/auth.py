from functools import wraps
from flask import Blueprint, session, redirect, url_for, flash, request, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import users

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = users.get(email)
        if user and check_password_hash(user['password'], password):
            session['user_id'] = email
            flash('Successfully logged in!', 'success')
            return redirect(url_for('main.index'))
        
        flash('Invalid email or password.', 'error')
    return render_template('login.html')

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if 'user_id' in session:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if email in users:
            flash('Email already registered.', 'error')
            return redirect(url_for('auth.signup'))
        
        hashed_password = generate_password_hash(password)
        users[email] = {'password': hashed_password}
        
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('signup.html')

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('auth.login'))
