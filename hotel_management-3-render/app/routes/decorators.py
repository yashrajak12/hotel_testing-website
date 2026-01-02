from functools import wraps
from flask_login import current_user
from flask import flash, redirect, url_for

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please login to access this page.', 'danger')
                return redirect(url_for('auth.login'))

            user_role = current_user.role.value.upper()  # ← UPPERCASE KAR DO
            required_roles = [r.upper() for r in roles]  # ← SABKO UPPERCASE

            if user_role not in required_roles:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('auth.dashboard'))

            return f(*args, **kwargs)
        return decorated_function
    return decorator