from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "TSRS - Trusted Sky Recognition System"
    secret_key: str = "change-me-in-production-use-256-bit-random-key"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480
    database_url: str = "sqlite:///./tsrs.db"
    face_match_threshold: float = 0.50  # Euclidean distance threshold for face-api.js 128-d descriptors
    cors_origins: list[str] = ["http://localhost:8080", "http://127.0.0.1:8080", "null"]

    class Config:
        env_file = ".env"


settings = Settings()
