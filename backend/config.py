from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    DATABASE_URL: str = f"sqlite:///{BASE_DIR}/data/opspilot.db"
    
    # AI Configuration
    AI_ENABLED: bool = True
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.5-flash"
    
    # Operational & Safety Limits
    MAX_TOOL_CALLS: int = 8
    MAX_AI_RESULT_ROWS: int = 100
    MAX_QUERY_SECONDS: int = 15
    MAX_DISPLAYED_ROWS: int = 500
    
    # Paths
    BASE_DIR: Path = BASE_DIR
    VECTOR_STORE_PATH: Path = BASE_DIR / "data" / "vector_store"
    SOURCES_DIR: Path = BASE_DIR / "data" / "sources"
    UPLOADS_DIR: Path = BASE_DIR / "data" / "uploads"
    EXPORTS_DIR: Path = BASE_DIR / "exports"
    LOGS_DIR: Path = BASE_DIR / "logs"
    
    # Safety & Privacy
    PII_REDACTION_ENABLED: bool = True
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

# Ensure required runtime directories exist
for folder in [settings.VECTOR_STORE_PATH, settings.SOURCES_DIR, settings.UPLOADS_DIR, settings.EXPORTS_DIR, settings.LOGS_DIR]:
    folder.mkdir(parents=True, exist_ok=True)
