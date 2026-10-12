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
