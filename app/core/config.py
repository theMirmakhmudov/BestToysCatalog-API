from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    DATABASE_URL: str = Field(..., validation_alias="DATABASE_URL")

    APP_DEFAULT_LANG: str = "uz"

    RATE_LIMIT_PUBLIC: str = "30/minute"
    RATE_LIMIT_AUTH: str = "120/minute"
    RATE_LIMIT_ADMIN: str = "300/minute"

    INIT_ADMIN_PHONE: str | None = None
    INIT_ADMIN_TELEGRAM_ID: int | None = None
    INIT_ADMIN_NAME: str | None = None

    SECRET_KEY: str = "change_this_secret_key_in_production"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
