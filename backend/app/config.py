from pathlib import Path

from pydantic_settings import BaseSettings

_env_files = []
for _candidate in [Path(__file__).resolve().parent.parent / ".env", Path(__file__).resolve().parent.parent.parent / ".env"]:
    if _candidate.is_file():
        _env_files.append(str(_candidate))


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite+aiosqlite:///./booksinsight.db"

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    openai_vision_model: str = "gpt-4o"

    # Clerk
    clerk_secret_key: str = ""
    clerk_jwks_url: str = ""

    # Server
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    cors_origins: str = "http://localhost:3000"

    # File storage
    upload_dir: str = "./uploads"
    max_upload_size_mb: int = 10

    # Tax engine
    default_tax_year: int = 2025

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    model_config = {"env_file": _env_files or ".env", "extra": "ignore"}


settings = Settings()
