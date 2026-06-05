# ============================================================
# config.py — ALL environment variables
# ============================================================

from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    # ── Neon PostgreSQL ──
    DATABASE_URL: str

    # ── GitHub ──
    GITHUB_TOKEN:       str
    GITHUB_REPO_OWNER:  str
    GITHUB_REPO_NAME:   str
    GITHUB_BRANCH:      str = "main"
    GITHUB_PDF_FOLDER:  str = "pdf"

    # ── Google OAuth ──
    GOOGLE_CLIENT_ID: str

    # ── Groq LLM ──
    GROQ_API_KEY: str

    # ── Qdrant Cloud ──
    QDRANT_URL:     str   # e.g. https://abc123.us-east4-0.gcp.cloud.qdrant.io
    QDRANT_API_KEY: str

    # ── App ──
    ALLOWED_ORIGINS: str = "*"

    class Config:
        env_file = ".env"
        extra="ignore"


settings = Settings()