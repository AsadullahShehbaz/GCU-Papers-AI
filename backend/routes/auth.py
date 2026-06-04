# ============================================================
# routes/auth.py — Google token verification
# Frontend sends Google ID token → we verify it → return user info
# ============================================================

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


# ── Request schema ────────────────────────────────────────────
class TokenRequest(BaseModel):
    token: str   # Google ID token from frontend


# ── Response schema ───────────────────────────────────────────
class UserInfo(BaseModel):
    email: str
    name:  str
    picture: str


# ── Route ─────────────────────────────────────────────────────
@router.post("/google", response_model=UserInfo)
async def verify_google_token(body: TokenRequest):
    """
    Verify Google ID token sent from frontend.
    Returns user info if valid, 401 if invalid.
    """
    try:
        info = id_token.verify_oauth2_token(
            body.token,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID,
        )
        return UserInfo(
            email=   info.get("email", ""),
            name=    info.get("name",  ""),
            picture= info.get("picture", ""),
        )
    except ValueError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")