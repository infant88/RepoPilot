import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "DemoStore API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Auth configuration
    # Note: Expects JWT_SECRET from environment. If missing in Docker container, defaults to empty!
    JWT_SECRET: str = os.getenv("JWT_SECRET", "super-secret-default-key-change-me")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/demodb")

    class Config:
        case_sensitive = True

settings = Settings()
