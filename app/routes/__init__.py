"""Routes package for the application."""
from flask import Blueprint

# Create blueprints
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
main_bp = Blueprint('main', __name__)
document_bp = Blueprint('document', __name__)

try:
    # Import routes to register them with blueprints
    from . import auth_routes
    from . import main_routes
    from . import document

    # Import error handlers
    from . import errors
except Exception as e:
    print(f"Error in routes/__init__.py: {str(e)}")
    import traceback
    traceback.print_exc()
