"""Main application routes."""
from flask import render_template, session, flash
from . import main_bp
from app.models.users import get_user_from_session
from app.models.history import get_user_history, get_user_documents

@main_bp.route('/')
def index():
    user = get_user_from_session(session)
    return render_template('index.html', user=user)

@main_bp.route('/history')
def user_history():
    if 'user_id' not in session:
        flash('Please log in to view your history.', 'error')
        return render_template('index.html')

    user = get_user_from_session(session)
    history = get_user_history(session['user_id'])
    documents = get_user_documents(session['user_id'])
    return render_template('history.html', user=user, history=history, documents=documents)
