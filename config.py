"""
Configuration settings for the Intelligent Library Chat Assistant
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration"""

    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

    # Database settings
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '3306')
    DB_NAME = os.getenv('DB_NAME', 'library_chatbot')
    DB_USER = os.getenv('DB_USER', 'chatbot_user')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')

    # SQLAlchemy settings
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///library_chatbot.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
    }

    # Redis settings (for session management)
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = os.getenv('REDIS_PORT', 6379)
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)

    # JWT settings for API authentication
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-me')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max file size
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')

    # Chatbot settings
    CHATBOT_NAME = "Babcock Library Assistant"
    CHATBOT_VERSION = "1.0.0"

    # NLP model settings
    SPACY_MODEL = "en_core_web_lg"
    SENTENCE_TRANSFORMER_MODEL = "all-MiniLM-L6-v2"

    # Rate limiting
    RATELIMIT_DEFAULT = "200 per day;50 per hour"
    RATELIMIT_STORAGE_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"

    # CORS settings
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')

    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.path.join(os.path.dirname(__file__), 'logs', 'app.log')

    # Performance settings
    MAX_RESPONSE_TIME = 4.0  # seconds
    CACHE_TIMEOUT = 300  # seconds

    # Evaluation metrics
    EVALUATION_ENABLED = True
    FEEDBACK_COLLECTION = True

    # Other settings
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    ENV = 'development'

    # Development-specific settings
    SQLALCHEMY_ECHO = True  # Log SQL queries
    CHATBOT_MODE = "development"


class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = False
    TESTING = True
    ENV = 'testing'

    # Use SQLite for testing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

    # Disable rate limiting for tests
    RATELIMIT_ENABLED = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    ENV = 'production'

    # Production-specific settings
    CHATBOT_MODE = "production"

    # Security settings
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True

    # Ensure secret keys are set
    SECRET_KEY = os.getenv('SECRET_KEY', 'prod-secret-key-change-me')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'prod-jwt-secret-key-change-me')
