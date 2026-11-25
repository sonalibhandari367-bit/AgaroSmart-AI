from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator


class Settings(BaseSettings):
    database_url: str = ""
    admin_api_token: str = ""
    cors_origins: str = "http://localhost:5173"
    max_upload_bytes: int = 5 * 1024 * 1024
    vercel: bool = False
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @model_validator(mode="after")
    def validate_hosted_database(self):
        if self.database_url.startswith("postgres://"):
            self.database_url = "postgresql+psycopg://" + self.database_url[len("postgres://"):]
        elif self.database_url.startswith("postgresql://"):
            self.database_url = "postgresql+psycopg://" + self.database_url[len("postgresql://"):]

        if not self.vercel and not self.database_url:
            self.database_url = "sqlite:///./agrosmart.db"
        elif self.vercel and self.database_url and not self.database_url.startswith("postgresql+psycopg://"):
            raise ValueError("Vercel requires DATABASE_URL with postgresql+psycopg://; local SQLite is not persistent on Vercel.")
        return self

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
