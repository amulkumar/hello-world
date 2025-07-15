from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )
    
    # Basic app settings
    APP_NAME: str = "Market Risk Management System"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Security settings
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    ALGORITHM: str = "HS256"
    
    # Database settings
    DATABASE_URL: str = "postgresql://risk_user:risk_password@localhost:5432/market_risk"
    TIMESCALE_URL: str = "postgresql://ts_user:ts_password@localhost:5433/timeseries_risk"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 0
    DATABASE_ECHO: bool = False
    
    # Redis settings
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_CACHE_TTL: int = 3600  # 1 hour
    
    # Message queue settings
    RABBITMQ_URL: str = "amqp://risk_queue:queue_password@localhost:5672"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # CORS settings
    ALLOWED_HOSTS: List[str] = ["*"]
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # Risk calculation settings
    DEFAULT_CONFIDENCE_LEVEL: float = 0.99
    DEFAULT_HOLDING_PERIOD: int = 1
    HISTORICAL_LOOKBACK_DAYS: int = 250
    MAX_MONTE_CARLO_SIMULATIONS: int = 10000
    
    # Data sources
    BLOOMBERG_API_URL: Optional[str] = None
    BLOOMBERG_API_KEY: Optional[str] = None
    REFINITIV_API_URL: Optional[str] = None
    REFINITIV_API_KEY: Optional[str] = None
    
    # File storage
    UPLOAD_DIRECTORY: str = "/tmp/uploads"
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_EXTENSIONS: List[str] = [".csv", ".xlsx", ".xls"]
    
    # Report generation
    REPORT_OUTPUT_DIRECTORY: str = "/tmp/reports"
    PDF_TIMEOUT: int = 60  # seconds
    
    # Monitoring and logging
    LOG_LEVEL: str = "INFO"
    ENABLE_METRICS: bool = True
    SENTRY_DSN: Optional[str] = None
    
    # Email settings for notifications
    SMTP_SERVER: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_USE_TLS: bool = True
    EMAIL_FROM: str = "risk-system@company.com"
    
    # Risk limits and alerts
    BREACH_NOTIFICATION_EMAILS: List[str] = []
    ESCALATION_DELAY_MINUTES: int = 15
    CRITICAL_BREACH_THRESHOLD: float = 1.2  # 120% of limit
    
    # Basel 2.5 specific settings
    VaR_CONFIDENCE_LEVELS: List[float] = [0.95, 0.99]
    STRESS_TEST_SCENARIOS: List[str] = [
        "2008_financial_crisis",
        "covid19_shock",
        "european_sovereign_crisis"
    ]
    
    # API rate limiting
    RATE_LIMIT_PER_MINUTE: int = 1000
    RATE_LIMIT_BURST: int = 100
    
    # Cache settings
    POSITION_CACHE_TTL: int = 300  # 5 minutes
    MARKET_DATA_CACHE_TTL: int = 60  # 1 minute
    RISK_CALCULATION_CACHE_TTL: int = 1800  # 30 minutes
    
    class Config:
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()