# ============================================================
# routes/auth.py — Google token verification
# Frontend sends Google ID token → we verify it → return user info
# ============================================================

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from config import settings

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger("gcul_api.auth")   # child of root logger in main.py


# ── Request schema ────────────────────────────────────────────
class TokenRequest(BaseModel):
    token: str


# ── Response schema ───────────────────────────────────────────
class UserInfo(BaseModel):
    email:   str
    name:    str
    picture: str


# ── Route ─────────────────────────────────────────────────────
@router.post("/google", response_model=UserInfo)
async def verify_google_token(body: TokenRequest):
    """
    Verify Google ID token sent from frontend.
    Returns user info if valid, 401 if invalid.
    """
    # Log only a token prefix — never log the full token
    token_preview = body.token[:12] + "..." if len(body.token) > 12 else "***"
    logger.info("AUTH | Verifying Google token  token_prefix=%s", token_preview)

    try:
        info = id_token.verify_oauth2_token(
            body.token,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID,
        )
    except ValueError as exc:
        logger.warning("AUTH | Token verification failed  reason='%s'", exc)
        raise HTTPException(status_code=401, detail=f"Invalid token: {exc}")
    except Exception:
        logger.exception("AUTH | Unexpected error during token verification")
        raise HTTPException(status_code=500, detail="Auth service error.")

    email = info.get("email", "")
    name  = info.get("name",  "")

    logger.info("AUTH | Token valid ✓  email=%s  name='%s'", email, name)

    return UserInfo(
        email=   email,
        name=    name,
        picture= info.get("picture", ""),
    )
