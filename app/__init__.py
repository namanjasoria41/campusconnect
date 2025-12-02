import os
from flask import Flask
from .extensions import db, migrate, login_manager
from .models import User  # import models for migrations
import re
from flask import Flask, url_for
from markupsafe import Markup
from .auth.routes import auth_bp
from .main.routes import main_bp

def create_app():
    app = Flask(__name__)
     
        # --- Hashtag link filter for Jinja ---
    def link_hashtags(text: str) -> str:
        if not text:
            return ""
        pattern = r"#(\w+)"
        def repl(match):
            tag = match.group(1)
            try:
                url = url_for("tags.view_tag", tag=tag.lower())
            except Exception:
                # If tags blueprint not ready yet, just return plain text hashtag
                return f"#{tag}"
            return f'<a href="{url}" class="hashtag-link">#{tag}</a>'
        return Markup(re.sub(pattern, repl, text))

    app.jinja_env.filters["link_hashtags"] = link_hashtags
    # --- end hashtag filter ---


    # Basic config
    app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "change-this-secret")
    app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://neondb_owner:npg_nzt7vXMb3hZr@ep-aged-unit-adh9nwak-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Uploads
    upload_folder = os.path.join(app.root_path, 'static', 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    app.config['UPLOAD_FOLDER'] = upload_folder

    # Razorpay key for frontend
    app.config['RAZORPAY_KEY_ID'] = os.environ.get("RAZORPAY_KEY_ID", "rzp_test_yourkeyid")

    # Init extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    login_manager.login_view = "auth.login"

    # Register blueprints
    from .auth.routes import auth_bp
    from .main.routes import main_bp
    from .profiles.routes import profiles_bp
    from .events.routes import events_bp
    from .swipe.routes import swipe_bp
    from .chat.routes import chat_bp
    from .billing.routes import billing_bp
    from .stories.routes import stories_bp
    from .gossip.routes import gossip_bp
    from .admin import admin_bp

    app.register_blueprint(stories_bp)
    app.register_blueprint(gossip_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(profiles_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(swipe_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(billing_bp)
    app.register_blueprint(admin_bp)

    return app
