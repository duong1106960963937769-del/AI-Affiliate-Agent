from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BASE_DIR.parent / ".env", extra="ignore")

    database_url: str = f"sqlite:///{BASE_DIR / 'data' / 'app.db'}"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    max_upload_mb: int = 5
    max_import_rows: int = 5000


settings = Settings()
