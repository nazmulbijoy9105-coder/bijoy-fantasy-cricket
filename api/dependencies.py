"""
dependencies.py — Role-based access control guards.
Role hierarchy: superadmin > admin > paid > free
"""
from fastapi import Depends, HTTPException, status
from .auth import get_current_user


def _require_role(allowed_roles: list[str]):
    async def guard(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {allowed_roles}",
            )
        return current_user
    return guard


# Convenience guards
require_paid        = _require_role(["paid", "admin", "superadmin"])
require_admin       = _require_role(["admin", "superadmin"])
require_superadmin  = _require_role(["superadmin"])
require_any         = get_current_user   # just logged in
