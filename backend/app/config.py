import os
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    # LLM Provider Configuration ("gemini", "groq", "openai", "custom")
    LLM_PROVIDER: str = "gemini"
    LLM_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    LLM_MODEL: str = "gemini-2.5-flash"
    FAST_MODEL: str = "gemini-2.5-flash"
    LLM_BASE_URL: str = ""
    LLM_TEMPERATURE: float = 0.1
    LLM_TIMEOUT_SECONDS: float = 35.0

    # GitHub Integration
    GITHUB_TOKEN: str = ""

    # Database & Storage
    DATABASE_URL: str = "sqlite+aiosqlite:///./changelens.db"
    WORKSPACE_TEMP_DIR: str = str(BASE_DIR / "temp_workspaces")

    # Safety Guardrails
    MAX_REPO_SIZE_MB: int = 500
    MAX_DIFF_LINES: int = 8000
    ALLOW_OFFLINE_FALLBACK: bool = False

    # Server Runtime
    ENVIRONMENT: str = "development"
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "https://*.netlify.app",
        "*"
    ]

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="allow"
    )

    def get_effective_api_key(self) -> str:
        """Resolves the active API key according to provider preference."""
        if self.LLM_API_KEY:
            return self.LLM_API_KEY
        provider = self.LLM_PROVIDER.lower()
        if provider == "gemini":
            return self.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
        elif provider == "groq":
            return self.GROQ_API_KEY or os.getenv("GROQ_API_KEY", "")
        elif provider == "openai":
            return self.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY", "")
        return (
            self.GEMINI_API_KEY
            or self.GROQ_API_KEY
            or self.OPENAI_API_KEY
            or os.getenv("GEMINI_API_KEY", "")
            or os.getenv("GROQ_API_KEY", "")
            or os.getenv("OPENAI_API_KEY", "")
        )

settings = Settings()
