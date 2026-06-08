from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Checkout Queue API"
    API_VERSION: str = "0.1.0"
    API_PREFIX: str = "/api/v1"
    DATABASE_URL: str = "postgresql+psycopg2://api-access:admin123@localhost:5432/checkout_queue"
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]
    SECRET_KEY: str = "change-this-secret-key"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 600
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    ML_MODEL_DIR: str = "ml_models"
    ML_MIN_TRAINING_SAMPLES: int = 50
    ENABLE_CHECKOUT_QUEUE: bool = True
    ENABLE_TRIAL_QUEUE: bool = True
    ENABLE_DEMO_TOOLS: bool = False
    ENABLE_IN_APP_SCHEDULER: bool = True
    NIGHTLY_QUEUE_CLEANUP_HOUR: int = 0
    NIGHTLY_QUEUE_CLEANUP_MINUTE: int = 5
    SCHEDULER_TIMEZONE: str = "Asia/Kolkata"
    MOCK_SMS_SHOULD_FAIL: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
