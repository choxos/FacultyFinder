import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv('/var/www/ff/.env')

class Config:
    """Base configuration class"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production'
    
    # Database Configuration
    DB_CONFIG = {
        'host': os.environ.get('DB_HOST', 'localhost'),
        'port': int(os.environ.get('DB_PORT', 5432)),
        'user': os.environ.get('DB_USER'),
        'password': os.environ.get('DB_PASSWORD'),
        'database': os.environ.get('DB_NAME')
    }
    
    # Application Configuration
    DEBUG = False
    TESTING = False
    PORT = int(os.environ.get('APP_PORT', 8008))
    HOST = os.environ.get('APP_HOST', '0.0.0.0')
    
    # Stripe Configuration
    STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')
    
    # Stripe Product/Price IDs
    STRIPE_SINGLE_ANALYSIS_PRICE_ID = os.environ.get('STRIPE_SINGLE_ANALYSIS_PRICE_ID')
    STRIPE_PACKAGE_PRICE_ID = os.environ.get('STRIPE_PACKAGE_PRICE_ID')
    STRIPE_PREMIUM_PRICE_ID = os.environ.get('STRIPE_PREMIUM_PRICE_ID')
    
    # AI API Keys (for paid users)
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
    GOOGLE_AI_API_KEY = os.environ.get('GOOGLE_AI_API_KEY')
    GROK_API_KEY = os.environ.get('GROK_API_KEY')
    
    # Email Configuration (for notifications)
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # Security Configuration
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour
    
    # Rate Limiting
    RATELIMIT_STORAGE_URL = 'redis://localhost:6379'
    RATELIMIT_DEFAULT = "1000 per hour"
    
    # Logging Configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = '/var/www/ff/logs/application.log'

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    DB_CONFIG = {
        'dev_mode': True,
        'db_path': '../database/facultyfinder_dev.db'
    }
    SESSION_COOKIE_SECURE = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DB_CONFIG = {
        'dev_mode': True,
        'db_path': ':memory:'  # In-memory database for tests
    }

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
} 