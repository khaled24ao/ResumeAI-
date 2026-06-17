"""Base configuration."""
import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class BaseConfig:
    ENVIRONMENT: str = os.getenv('ENVIRONMENT', 'development')
    DEBUG: bool = os.getenv('DEBUG', 'False').lower() == 'true'
    TESTING: bool = False
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
    DATABASE_URL: str = os.getenv('DATABASE_URL', 'sqlite:///resume_ai.db')
    REDIS_URL: str = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    GROQ_API_KEY: str = os.getenv('GROQ_API_KEY', '')
    UPLOAD_FOLDER: str = os.getenv('UPLOAD_FOLDER', 'uploads')
    MAX_CONTENT_LENGTH: int = 50 * 1024 * 1024
    CORS_ORIGINS: list = ['http://localhost:3000', 'http://localhost:5000']
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    SENTRY_DSN: Optional[str] = os.getenv('SENTRY_DSN')

    def validate(self) -> list:
        warnings = []
        if not self.GROQ_API_KEY and not self.TESTING:
            warnings.append('GROQ_API_KEY not set')
        if self.DEBUG and self.ENVIRONMENT == 'production':
            warnings.append('DEBUG enabled in production')
        return warnings
