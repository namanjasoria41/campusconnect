from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user, login_required


def require_plan(min_plan: str):
    def decorator(f):
        @wraps(f)
        @login_required
        def wrapper(*args, **kwargs):
            if not current_user.has_plan(min_plan):
                flash(f"This feature requires {min_plan.capitalize()} plan.", "warning")
                return redirect(url_for("billing.pricing"))
            return f(*args, **kwargs)
        return wrapper
    return decorator
