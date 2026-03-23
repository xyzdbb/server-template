from functools import lru_cache
from typing import List, Literal
from urllib.parse import quote_plus

from pydantic import Field, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

    PROJECT_NAME: str = "FastAPI Backend"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: Literal["development", "staging", "production", "test"] = "development"
    
    SECRET_KEY: str = Field(min_length=32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 10080
    
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: int = 5432
    
    @computed_field  # type: ignore[prop-decorator]
    @property
    def DATABASE_URL(self) -> str:
        user = quote_plus(self.POSTGRES_USER)
        password = quote_plus(self.POSTGRES_PASSWORD)
        return (
            f"postgresql+psycopg://{user}:{password}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    REDIS_URL: str = "redis://localhost:6379/0"

    TRUSTED_HOSTS: List[str] = ["127.0.0.1"]

    BACKEND_CORS_ORIGINS: List[str] = []

    @field_validator("TRUSTED_HOSTS", "BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def split_comma_separated(cls, v: str | List[str]) -> List[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v

    @field_validator("BACKEND_CORS_ORIGINS")
    @classmethod
    def validate_cors_origins(cls, v: List[str]) -> List[str]:
        for origin in v:
            if origin == "*":
                raise ValueError(
                    "Wildcard '*' is not allowed in CORS origins "
                    "because allow_credentials=True (per CORS spec). "
                    "Please list explicit origins instead."
                )
            if not origin.startswith(("http://", "https://")):
                raise ValueError(f"Invalid CORS origin: {origin!r}, must start with http:// or https://")
        return [origin.rstrip("/") for origin in v]
    
    FIRST_SUPERUSER: str
    FIRST_SUPERUSER_PASSWORD: str
    FIRST_SUPERUSER_FULL_NAME: str = "Admin User"
    
    @computed_field  # type: ignore[prop-decorator]
    @property
    def IS_PRODUCTION(self) -> bool:
        return self.ENVIRONMENT == "production"

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
