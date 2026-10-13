from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Secure Organization Management Platform"
    app_env: str = "development"
    debug: bool = False
    database_url: str = ""
    mfa_encryption_key: str = ""

    mfa_challenge_ttl_seconds: int = 300
    session_lifetime_seconds: int = 3600
    password_recovery_token_ttl_seconds: int = 1800

    # Password-recovery abuse protection
    password_recovery_rate_limit_hmac_key: str = ""
    password_recovery_source_rate_limit: int = Field(default=10, gt=0)
    password_recovery_source_window_seconds: int = Field(default=900, gt=0)
    password_recovery_email_rate_limit: int = Field(default=3, gt=0)
    password_recovery_email_window_seconds: int = Field(default=3600, gt=0)
    password_reset_source_rate_limit: int = Field(default=10, gt=0)
    password_reset_source_window_seconds: int = Field(default=900, gt=0)

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    smtp_starttls: bool = True
    smtp_use_ssl: bool = False
    smtp_timeout_seconds: int = 10

    password_reset_url: str = "http://localhost:3000/reset-password"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
