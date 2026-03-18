"""
payment.py — Bcash & Nagad subscription flow.
Skeleton: replace placeholder API calls with real gateway SDKs.

Flow:
  1. POST /subscribe/{gateway}  → creates pending sub, returns payment ref
  2. Gateway redirects to callback URL
  3. POST /payment/callback     → confirms, assigns API key + paid role
"""
import yaml, secrets
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from .database import query_db, execute_db
from .auth import get_current_user, generate_api_key

BASE_DIR = Path(__file__).resolve().parent.parent
with open(BASE_DIR / "config.yaml") as f:
    _cfg = yaml.safe_load(f)

router = APIRouter(prefix="/api/v1/payment", tags=["Payment"])

PLANS = {
    "monthly": _cfg["subscriptions"]["monthly_price_bdt"],
    "yearly":  _cfg["subscriptions"]["yearly_price_bdt"],
}
PLAN_DAYS = {"monthly": 30, "yearly": 365}
GATEWAYS  = ["bcash", "nagad"]


class SubscribeRequest(BaseModel):
    plan:    str = "monthly"   # monthly | yearly
    gateway: str               # bcash | nagad


class CallbackPayload(BaseModel):
    payment_reference: str
    status: str                # completed | failed


# ─────────────────────────────────────────────────────────────
@router.post("/subscribe")
async def subscribe(
    req: SubscribeRequest,
    current_user: dict = Depends(get_current_user),
):
    """Initiate a subscription. Returns payment reference + gateway URL."""
    if req.gateway not in GATEWAYS:
        raise HTTPException(status_code=400, detail=f"Gateway must be one of {GATEWAYS}")
    if req.plan not in PLANS:
        raise HTTPException(status_code=400, detail=f"Plan must be one of {list(PLANS.keys())}")

    amount    = PLANS[req.plan]
    pay_ref   = "BPL-" + secrets.token_hex(12).upper()

    execute_db(
        """INSERT INTO subscriptions
           (user_id, plan, payment_gateway, payment_reference, status, amount_bdt)
           VALUES (?,?,?,?,?,?)""",
        (current_user["user_id"], req.plan, req.gateway, pay_ref, "pending", amount),
    )

    # ── REAL INTEGRATION POINT ──────────────────────────────
    # For Bcash:  POST to _cfg["payment"]["bcash"]["api_url"] with merchant credentials
    # For Nagad:  POST to _cfg["payment"]["nagad"]["api_url"] with merchant credentials
    # Both return a redirect URL → send that to the client.
    # ────────────────────────────────────────────────────────
    gateway_url = f"https://sandbox.{req.gateway}.com.bd/pay?ref={pay_ref}&amount={amount}"

    return {
        "payment_reference": pay_ref,
        "gateway":           req.gateway,
        "plan":              req.plan,
        "amount_bdt":        amount,
        "redirect_url":      gateway_url,   # replace with real gateway URL
        "message":           "Redirect user to redirect_url to complete payment.",
    }


@router.post("/callback")
async def payment_callback(payload: CallbackPayload):
    """
    Called by the payment gateway webhook after user completes/fails payment.
    In production: verify HMAC signature from gateway before trusting this.
    """
    rows = query_db(
        "SELECT * FROM subscriptions WHERE payment_reference=?",
        (payload.payment_reference,),
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Subscription not found")

    sub     = rows[0]
    user_id = sub["user_id"]

    if payload.status == "completed":
        api_key    = generate_api_key()
        start_date = datetime.utcnow().date()
        expiry     = start_date + timedelta(days=PLAN_DAYS.get(sub["plan"], 30))

        execute_db(
            "UPDATE users SET api_key=?, role='paid', updated_at=CURRENT_TIMESTAMP WHERE user_id=?",
            (api_key, user_id),
        )
        execute_db(
            """UPDATE subscriptions
               SET status='completed', start_date=?, expiry_date=?
               WHERE payment_reference=?""",
            (start_date, expiry, payload.payment_reference),
        )
        return {
            "message":    "Payment confirmed. API key issued.",
            "api_key":    api_key,
            "expires_on": str(expiry),
        }

    # Payment failed
    execute_db(
        "UPDATE subscriptions SET status='failed' WHERE payment_reference=?",
        (payload.payment_reference,),
    )
    return {"message": "Payment failed. Please retry."}


@router.get("/status/{payment_reference}")
async def payment_status(
    payment_reference: str,
    current_user: dict = Depends(get_current_user),
):
    rows = query_db(
        "SELECT * FROM subscriptions WHERE payment_reference=? AND user_id=?",
        (payment_reference, current_user["user_id"]),
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Not found")
    return rows[0]


@router.get("/my-subscription")
async def my_subscription(current_user: dict = Depends(get_current_user)):
    rows = query_db(
        "SELECT * FROM subscriptions WHERE user_id=? ORDER BY created_at DESC LIMIT 1",
        (current_user["user_id"],),
    )
    return rows[0] if rows else {"message": "No subscription found"}
