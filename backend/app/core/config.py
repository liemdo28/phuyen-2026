from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()
BASE_DIR = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    app_env: str = os.getenv("APP_ENV", "development")
    app_port: int = int(os.getenv("APP_PORT", "8000"))
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_webhook_secret: str = os.getenv("TELEGRAM_WEBHOOK_SECRET", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    anthropic_model: str = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")
    google_service_account_json: str = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "")
    default_spreadsheet_id: str = os.getenv("DEFAULT_SPREADSHEET_ID", "")
    default_spreadsheet_url: str = os.getenv("DEFAULT_SPREADSHEET_URL", "")
    sheets_webapp_url: str = os.getenv("SHEETS_WEBAPP_URL", "")
    sheets_api_secret: str = os.getenv("SHEETS_API_SECRET", "")
    redis_url: str = os.getenv("REDIS_URL", "")
    postgres_dsn: str = os.getenv("POSTGRES_DSN", "")
    weather_api_key: str = os.getenv("WEATHER_API_KEY", "")
    maps_api_key: str = os.getenv("MAPS_API_KEY", "")
    events_api_key: str = os.getenv("EVENTS_API_KEY", "")
    local_business_api_key: str = os.getenv("LOCAL_BUSINESS_API_KEY", "")
    beach_conditions_api_url: str = os.getenv("BEACH_CONDITIONS_API_URL", "")
    vector_db_url: str = os.getenv("VECTOR_DB_URL", "")
    vector_db_api_key: str = os.getenv("VECTOR_DB_API_KEY", "")
    state_dir: str = os.getenv("STATE_DIR", str(BASE_DIR / ".state"))
    db_path: str = os.getenv("DB_PATH", str(BASE_DIR / ".state" / "telegram_ai.sqlite3"))
    queue_backend: str = os.getenv("QUEUE_BACKEND", "inline")
    rate_limit_window_seconds: int = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "10"))
    rate_limit_max_messages: int = int(os.getenv("RATE_LIMIT_MAX_MESSAGES", "4"))
    repeated_text_limit: int = int(os.getenv("REPEATED_TEXT_LIMIT", "2"))


settings = Settings()
