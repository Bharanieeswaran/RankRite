"""
Configuration settings for RankRite Resume Ranker
"""
import os
from datetime import timedelta

class Config:
    """Base configuration class"""

    # Get the base directory of the application (where config.py resides)
    # This ensures paths are absolute and consistent, regardless of current working directory
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'rankrite-secret-key-2024-dev'

    # Database
    # Use an absolute path for the SQLite database to avoid 'unable to open database file' issues
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'resume_ranker.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- THIS IS THE DEBUG PRINT LINE I NEED TO SEE IN YOUR OUTPUT ---
    print(f"DEBUG (config.py): Database URI set to: {SQLALCHEMY_DATABASE_URI}")
    # --- END DEBUG PRINT ---

    # File uploads
    # Ensure these paths are also absolute relative to the BASE_DIR for consistency
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    REPORTS_FOLDER = os.path.join(BASE_DIR, 'reports')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc'}

    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)

    # Application settings
    JOBS_PER_PAGE = 10
    RESUMES_PER_PAGE = 20

    # NLP Settings
    MIN_SIMILARITY_THRESHOLD = 0.1
    TOP_SKILLS_COUNT = 10

    # Email settings (for future use)
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False

    # Enhanced security for production
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:' # Use in-memory DB for tests

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}