"""
auth.py — JWT + bcrypt auth. API-key auth for paid endpoints.
"""
import secrets
import yaml
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from jose import JWTError, jwt
from passlib.context import CryptContext

from .database import query_db, execute_db

BASE_DIR = Path(__file__).resolve().parent.parent
with open(BASE_DIR / "config.yaml") as f:
    _cfg = yaml.safe_load(f)

SECRET_KEY = _cfg["auth"]["secret_key"]
ALGORITHM  = _cfg["auth"]["algorithm"]
TOKEN_EXP  = _cfg["auth"]["access_token_expire_minutes"]

pwd_ctx       = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)
api_key_hdr   = APIKeyHeader(name="X-API-Key", auto_error=False)


# ── password helpers ──────────────────────────────────────────
def hash_password(plain: str) -> str:
    return pwd_ctx.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)


# ── token helpers ─────────────────────────────────────────────
def create_access_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(minutes=TOKEN_EXP)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def generate_api_key() -> str:
    return secrets.token_urlsafe(32)


# ── user fetchers ─────────────────────────────────────────────
def get_user_by_username(username: str) -> dict | None:
    rows = query_db("SELECT * FROM users WHERE username=? AND is_active=1", (username,))
    return rows[0] if rows else None

def get_user_by_id(user_id: int) -> dict | None:
    rows = query_db("SELECT * FROM users WHERE user_id=? AND is_active=1", (user_id,))
    return rows[0] if rows else None

def get_user_by_api_key(key: str) -> dict | None:
    rows = query_db("SELECT * FROM users WHERE api_key=? AND is_active=1", (key,))
    return rows[0] if rows else None


# ── dependency: current user (JWT or API key) ─────────────────
async def get_current_user(
    token:   str | None = Depends(oauth2_scheme),
    api_key: str | None = Depends(api_key_hdr),
) -> dict:
    # Try API-key first
    if api_key:
        user = get_user_by_api_key(api_key)
        if user:
            return user

    # Try JWT
    if token:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            uid = payload.get("sub")
            if uid:
                user = get_user_by_id(int(uid))
                if user:
                    return user
        except JWTError:
            pass

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


# ── optional auth (free endpoints still work anonymously) ─────
async def optional_user(
    token:   str | None = Depends(oauth2_scheme),
    api_key: str | None = Depends(api_key_hdr),
) -> dict | None:
    try:
        return await get_current_user(token=token, api_key=api_key)
    except HTTPException:
        return None
