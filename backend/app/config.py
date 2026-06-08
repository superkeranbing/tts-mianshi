import os
from functools import lru_cache

from pydantic_settings import BaseSettings

APP_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(APP_DIR)
ENV_FILE = os.path.join(BACKEND_DIR, ".env")


class Settings(BaseSettings):
    APP_NAME: str = "听记面试 ASR-Mianshi"
    DEBUG: bool = True
    VERSION: str = "1.0.0"

    # Database - SQLite for local dev
    DATABASE_URL: str = "postgresql://dev:dev123@localhost:5432/asr_mianshi"
    SYNC_DATABASE_URL: str = "postgresql://dev:dev123@localhost:5432/asr_mianshi"

    # JWT
    JWT_SECRET: str = "asr-mianshi-dev-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440

    # File storage (local filesystem instead of MinIO)
    UPLOAD_DIR: str = os.path.join(BACKEND_DIR, "uploads")
    AUDIO_DIR: str = os.path.join(BACKEND_DIR, "uploads", "audio")
    RESUME_DIR: str = os.path.join(BACKEND_DIR, "uploads", "resumes")
    EXPORT_DIR: str = os.path.join(BACKEND_DIR, "uploads", "exports")

    # Redis / Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # ASR
    ASR_BACKEND: str = "funasr"
    ASR_MODEL_DIR: str = "./models/funasr"

    # LLM
    LLM_BASE_URL: str = "https://api.deepseek.com/v1"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "deepseek-chat"
    LLM_MAX_TOKENS: int = 4096

    # Storage backend: local | minio
    STORAGE_BACKEND: str = "local"

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:1420,http://localhost:8000"

    # MinIO
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "asr-mianshi"

    class Config:
        env_file = ENV_FILE
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
