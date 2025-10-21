from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # Database
    database_url: str = ""

    # Redis
    redis_url: str = ""

    # Telegram
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    telegram_api_url: str = ""

    # Email
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    from_email: str = ""
    
    # Google Calendar API
    google_calendar_id: str = "vi.vietnamese#holiday@group.v.calendar.google.com"  # Vietnam holidays calendar
    google_api_key: str = ""  # API key for public calendar access
    
    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = ""  # Will be loaded from .env


    # Application
    secret_key: str = ""
    debug: bool = False
    host: str = ""
    port: int = 8000
    
    # Notifications
    notification_time: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
