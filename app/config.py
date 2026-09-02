"""Application configuration."""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True

    # Google OAuth 2.0
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')

    # Session / cookie hardening
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_HTTPONLY = True

    # Critical incident email alert settings
    EMAIL_ALERTS_ENABLED = os.environ.get('EMAIL_ALERTS_ENABLED', '1').lower() in ('1', 'true', 'yes', 'on')
    INCIDENT_ALERT_SEVERITY = os.environ.get('INCIDENT_ALERT_SEVERITY', 'critical').lower()
    INCIDENT_ALERT_EMAIL_TO = os.environ.get('INCIDENT_ALERT_EMAIL_TO', 'allayedicko4@gmail.com')
    SMTP_SERVER = os.environ.get('SMTP_SERVER', '')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
    SMTP_USE_TLS = os.environ.get('SMTP_USE_TLS', '1').lower() in ('1', 'true', 'yes', 'on')
    SMTP_USERNAME = os.environ.get('SMTP_USERNAME', '')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
    SMTP_FROM_EMAIL = os.environ.get('SMTP_FROM_EMAIL', SMTP_USERNAME or 'noreply@itsupport.local')


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///dev.db')
    SESSION_COOKIE_SECURE = False


class TestingConfig(Config):
    TESTING = True
    EMAIL_ALERTS_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False
    # Share one connection so all requests see the same in-memory DB
    SQLALCHEMY_ENGINE_OPTIONS = {
        'connect_args': {'check_same_thread': False},
        'poolclass': __import__('sqlalchemy.pool', fromlist=['StaticPool']).StaticPool,
    }


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}
