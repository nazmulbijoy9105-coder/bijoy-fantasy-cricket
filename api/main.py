"""
api/main.py  –  FastAPI application entry point
Run: uvicorn api.main:app --reload
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm

from .auth import (authenticate_user, create_access_token,
                   hash_password, UserCreate, UserOut, Token)
from .database import execute_db, query_one
from .payment import router as payment_router
from .admin_dashboard import router as admin_router
from .endpoints.teams import router as teams_router
from .endpoints.players import router as players_router
from .endpoints.matches import router as matches_router
from .endpoints.premium import router as premium_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    db_path = os.getenv("DATABASE_PATH", "bpl.db")
    if not os.path.exists(db_path):
        try:
            from database.migrate import run as migrate
            migrate()
        except Exception as e:
            print(f"[startup] Migration error: {e}")
    yield


app = FastAPI(
    title="BPL Cricket Stats API",
    description=(
        "Bangladesh Premier League (BPL) cricket statistics API 2012-2026. "
        "Numeric stats only. Free & premium tiers. Powered by FastAPI."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def audit_middleware(request: Request, call_next):
    response = await call_next(request)
    try:
        execute_db(
            "INSERT INTO audit_log(endpoint,method,status_code,ip_address) VALUES(?,?,?,?)",
            (str(request.url.path), request.method, response.status_code,
             request.client.host if request.client else "unknown"),
        )
    except Exception:
        pass
    return response


app.include_router(teams_router,   prefix="/bpl")
app.include_router(players_router, prefix="/bpl")
app.include_router(matches_router, prefix="/bpl")
app.include_router(premium_router, prefix="/bpl")
app.include_router(payment_router)
app.include_router(admin_router)


@app.post("/auth/register", tags=["Auth"])
def register(user: UserCreate):
    if query_one("SELECT 1 FROM users WHERE username=?", (user.username,)):
        raise HTTPException(status_code=400, detail="Username already taken.")
    uid = execute_db(
        "INSERT INTO users(username,email,password,role) VALUES(?,?,?,?)",
        (user.username, user.email, hash_password(user.password), "free"),
    )
    return query_one("SELECT user_id,username,email,role,created_at FROM users WHERE user_id=?", (uid,))


@app.post("/auth/token", response_model=Token, tags=["Auth"])
def login(form: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form.username, form.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token({"sub": user["username"]})
    return {"access_token": token, "token_type": "bearer"}


@app.get("/health", tags=["System"])
def health():
    return {"status": "ok", "service": "BPL Cricket Stats API", "version": "1.0.0"}


@app.get("/", tags=["System"])
def root():
    return {
        "message": "Welcome to BPL Cricket Stats API",
        "docs": "/docs",
        "version": "1.0.0",
        "seasons": "2012-2026",
        "free_endpoints": ["/bpl/teams", "/bpl/players", "/bpl/matches"],
        "premium_endpoints": ["/bpl/premium/predictions/{match_id}", "/bpl/premium/player-compare"],
    }
