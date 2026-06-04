# ============================================================
# config.py — ALL environment variables live here
# Change behaviour by editing .env, never touch this file
# ============================================================

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- Neon PostgreSQL ---
    DATABASE_URL: str

    # --- GitHub ---
    GITHUB_TOKEN: str
    GITHUB_REPO_OWNER: str        # your GitHub username
    GITHUB_REPO_NAME: str         # repo where PDFs are stored
    GITHUB_BRANCH: str = "main"   # branch to upload to
    GITHUB_PDF_FOLDER: str = "pdf" # folder inside repo

    # --- Google OAuth ---
    GOOGLE_CLIENT_ID: str

    # --- App ---
    ALLOWED_ORIGINS: str = "*"    # comma separated, e.g. "https://yoursite.com"

    class Config:
        env_file = ".env"         # reads from .env file automatically


# Single instance — import this everywhere
settings = Settings()