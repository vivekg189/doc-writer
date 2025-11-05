from flask import Blueprint, render_template, session
from ..auth import login_required

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html', user=session.get('user_id'))
