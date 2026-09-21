"""
Application configuration.
Centralizes all config values so they can be changed in one place.
"""
import os


class Config:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

    # Secret key for session management and CSRF protection
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # SQLite database path
    DATABASE = os.path.join(BASE_DIR, 'database', 'platform.db')

    # File upload settings
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload size

    # AI Integration
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
