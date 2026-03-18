"""
admin_dashboard.py — Superadmin & admin endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from .database import query_db, execute_db
from .dependencies import require_admin, require_superadmin

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])


@router.get("/stats")
async def dashboard_stats(_=Depends(require_admin)):
    """High-level platform stats."""
    users      = query_db("SELECT COUNT(*) as n FROM users")[0]["n"]
    paid       = query_db("SELECT COUNT(*) as n FROM users WHERE role='paid'")[0]["n"]
    subs       = query_db("SELECT COUNT(*) as n FROM subscriptions WHERE status='completed'")[0]["n"]
    revenue    = query_db("SELECT COALESCE(SUM(amount_bdt),0) as t FROM subscriptions WHERE status='completed'")[0]["t"]
    matches    = query_db("SELECT COUNT(*) as n FROM matches")[0]["n"]
    players    = query_db("SELECT COUNT(*) as n FROM players")[0]["n"]
    return {
        "total_users":    users,
        "paid_users":     paid,
        "free_users":     users - paid,
        "completed_subs": subs,
        "total_revenue_bdt": revenue,
        "total_matches":  matches,
        "total_players":  players,
    }


@router.get("/users")
async def list_users(limit: int = 50, offset: int = 0, _=Depends(require_admin)):
    return query_db(
        "SELECT user_id,username,email,role,is_active,created_at FROM users ORDER BY created_at DESC LIMIT ? OFFSET ?",
        (limit, offset),
    )


@router.post("/users/{user_id}/deactivate")
async def deactivate_user(user_id: int, _=Depends(require_superadmin)):
    execute_db("UPDATE users SET is_active=0 WHERE user_id=?", (user_id,))
    return {"message": "User deactivated"}


@router.post("/users/{user_id}/role")
async def set_role(user_id: int, role: str, _=Depends(require_superadmin)):
    allowed = ["free", "paid", "admin", "superadmin"]
    if role not in allowed:
        raise HTTPException(status_code=400, detail=f"Role must be one of {allowed}")
    execute_db("UPDATE users SET role=? WHERE user_id=?", (role, user_id))
    return {"message": f"Role updated to {role}"}


@router.post("/users/{user_id}/revoke-key")
async def revoke_api_key(user_id: int, _=Depends(require_admin)):
    execute_db("UPDATE users SET api_key=NULL WHERE user_id=?", (user_id,))
    return {"message": "API key revoked"}


@router.get("/subscriptions")
async def list_subscriptions(
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
    _=Depends(require_admin),
):
    if status:
        return query_db(
            "SELECT * FROM subscriptions WHERE status=? ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (status, limit, offset),
        )
    return query_db(
        "SELECT * FROM subscriptions ORDER BY created_at DESC LIMIT ? OFFSET ?",
        (limit, offset),
    )


@router.get("/audit-log")
async def audit_log(limit: int = 100, _=Depends(require_admin)):
    """Placeholder — wire to a real audit_log table in production."""
    return {"message": "Audit log endpoint ready. Implement audit_log table for full tracking."}
