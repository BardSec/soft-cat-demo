import os
import secrets


class Config:
    # Use a fixed demo key so the app starts without any setup.
    # For production use, override with a strong SECRET_KEY env var.
    SECRET_KEY = os.environ.get("SECRET_KEY", secrets.token_hex(32))
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:////app/instance/catalog.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
