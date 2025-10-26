from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    DATABASE_URL: str = Field(..., validation_alias="DATABASE_URL")
    JWT_SECRET: str = "changeme"
    JWT_ALG: str = "HS256"
    ACCESS_TTL_SECONDS: int = 3600
    REFRESH_TTL_SECONDS: int = 2592000
    APP_DEFAULT_LANG: str = "uz"

    RATE_LIMIT_PUBLIC: str = "30/minute"
    RATE_LIMIT_AUTH: str = "120/minute"
    RATE_LIMIT_ADMIN: str = "300/minute"

    INIT_ADMIN_EMAIL: str | None = None
    INIT_ADMIN_PHONE: str | None = None
    INIT_ADMIN_PASSWORD: str | None = None
    INIT_ADMIN_NAME: str | None = None

    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM: str | None = None
    SMTP_FROM_NAME: str | None = "ObidovToys"
    SMTP_TLS: bool = True

    class Config:
        env_file = ".env"

settings = Settings()
