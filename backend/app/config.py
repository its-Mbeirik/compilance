from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DEEPSEEK_API_KEY: str
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"
    DEEPSEEK_MODEL: str = "deepseek-chat"

    DATABASE_URL: str
    POSTGRES_USER: str = "conformite"
    POSTGRES_PASSWORD: str = "conformite_dev_password_change_me"
    POSTGRES_DB: str = "conformite"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    EMBEDDING_MODEL: str = "BAAI/bge-m3"
    EMBEDDING_DIMENSION: int = 1024

    BACKEND_PORT: int = 8000
    FRONTEND_PORT: int = 3000
    LOG_LEVEL: str = "INFO"

    CORPUS_DIR: Path = PROJECT_ROOT / "ressourse" / "ressourse"
    UPLOADS_DIR: Path = PROJECT_ROOT / "data" / "uploads"
    EMBEDDINGS_CACHE_DIR: Path = Path(r"C:\Users\chico\AppData\Local\AssistConformite\hf_cache")


settings = Settings()

settings.UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
settings.EMBEDDINGS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
