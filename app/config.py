import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "developer-secret-key-change-this"

    # Database (use SQLite by default)
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or "sqlite:///app.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Secret code required to create admin
    ADMIN_SETUP_CODE = "campusconnect-superadmin-2025"

