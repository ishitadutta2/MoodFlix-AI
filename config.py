"""
config.py
----------------------------
Application Configuration
MoodFlix AI
"""

import os
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

APP_VERSION = "5.0.0"


class Config:
    """Base Configuration"""

    # Flask
    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "change-this-secret-key"
    )

    # Gemini API
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    # MongoDB
    MONGO_URI = os.getenv(
        "MONGODB_URI",
        os.getenv("MONGO_URI", "mongodb://localhost:27017/moodflix")
    )

    # Flask
    DEBUG = False

    # Session
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False      # Change to True in production (HTTPS)
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = 86400  # 1 day

    # Uploads
    UPLOAD_FOLDER = "static/uploads"

    # Maximum Upload Size (5 MB)
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True


class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    RATELIMIT_ENABLED = False


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}