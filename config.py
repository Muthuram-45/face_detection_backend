import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load environment variables from .env file
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path)

def build_database_url() -> str:
    # Check if direct DATABASE_URL is provided
    direct_url = os.getenv("DATABASE_URL")
    if direct_url:
        if direct_url.startswith("postgres://"):
            return direct_url.replace("postgres://", "postgresql://", 1)
        return direct_url

    # Check for individual Neon / PostgreSQL environment variables
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT", "5432")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_name = os.getenv("DB_NAME", "neondb")
    db_ssl = os.getenv("DB_SSL", "true").lower() in ["true", "1", "yes"]

    if db_host and db_user and db_password:
        ssl_mode = "?sslmode=require" if db_ssl else ""
        return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}{ssl_mode}"

    # Default fallback to SQLite
    return "sqlite:///./attendance.db"

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Face-Based Attendance System"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-key-change-in-production-123456789")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Database URL
    DATABASE_URL: str = build_database_url()
    
    # AI Service URL
    AI_SERVICE_URL: str = os.getenv("AI_SERVICE_URL", "http://127.0.0.1:8001")
    
    # File Storage
    UPLOAD_DIR: str = os.path.join(os.path.dirname(__file__), "uploads")
    
    # Late Threshold (Default 9:15 AM format HH:MM)
    DEFAULT_LATE_THRESHOLD: str = "09:15"
    FACE_CONFIDENCE_THRESHOLD: float = 0.65

    class Config:
        case_sensitive = True

settings = Settings()
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(os.path.join(settings.UPLOAD_DIR, "students"), exist_ok=True)
os.makedirs(os.path.join(settings.UPLOAD_DIR, "unknown"), exist_ok=True)
