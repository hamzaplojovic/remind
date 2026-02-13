"""Polar webhook handler for processing payments and creating users."""

import hashlib
import hmac
import logging
import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Request, HTTPException
from sqlalchemy import text

from remind_backend.config import get_settings
from remind_backend.database import get_engine
from remind_backend.email import send_license_email

logger = logging.getLogger(__name__)
router = APIRouter()

# Map Polar product IDs to plan tiers (resolved at request time)
def _get_product_tier_map() -> dict[str, str]:
    settings = get_settings()
    return {
        settings.polar_product_free: "free",
        settings.polar_product_indie: "indie",
        settings.polar_product_pro: "pro",
        settings.polar_product_team: "team",
    }


def _generate_token(plan_tier: str) -> str:
    return f"remind_{plan_tier}_{secrets.token_hex(12)}"


def _verify_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify Polar webhook signature."""
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


@router.post("/polar")
async def polar_webhook(request: Request):
    """Handle Polar payment webhooks.

    Polar sends events like 'order.created' when a customer completes checkout.
    We create a user and email them their license token.
    """
    settings = get_settings()
    body = await request.body()

    # Verify webhook signature if secret is configured
    signature = request.headers.get("webhook-signature", "")
    if settings.polar_webhook_secret and signature:
        if not _verify_signature(body, signature, settings.polar_webhook_secret):
            logger.warning("Invalid webhook signature")
            raise HTTPException(status_code=401, detail="Invalid signature")

    payload = await request.json()
    event_type = payload.get("type", "")

    logger.info("Polar webhook received: %s", event_type)

    # Handle order completion
    if event_type in ("order.created", "subscription.created"):
        await _handle_order(payload.get("data", {}))
    else:
        logger.info("Ignoring event type: %s", event_type)

    return {"status": "ok"}


async def _handle_order(data: dict):
    """Process a completed order — create user and email token."""
    # Extract customer info
    customer = data.get("customer", {})
    email = customer.get("email") or data.get("customer_email")
    if not email:
        logger.error("No email in webhook payload: %s", data)
        return

    # Determine plan tier from product ID
    product = data.get("product", {})
    product_id = product.get("id", "")
    tier_map = _get_product_tier_map()
    plan_tier = tier_map.get(product_id, "free")

    logger.info("Creating user: email=%s plan=%s product_id=%s", email, plan_tier, product_id)

    # Generate token and insert user
    token = _generate_token(plan_tier)
    now = datetime.now(timezone.utc)
    engine = get_engine()

    with engine.connect() as conn:
        # Check if user with this email already exists
        result = conn.execute(
            text("SELECT id, token, plan_tier FROM users WHERE email = :email"),
            {"email": email},
        )
        existing = result.fetchone()

        if existing:
            # Upgrade existing user
            conn.execute(
                text(
                    "UPDATE users SET plan_tier = :plan_tier, active = true, updated_at = :now "
                    "WHERE email = :email"
                ),
                {"plan_tier": plan_tier, "now": now, "email": email},
            )
            conn.commit()
            token = existing.token  # Keep their existing token
            logger.info("Upgraded existing user %s to %s", email, plan_tier)
        else:
            # Create new user
            conn.execute(
                text(
                    "INSERT INTO users (token, email, plan_tier, created_at, updated_at, active) "
                    "VALUES (:token, :email, :plan_tier, :created_at, :updated_at, :active)"
                ),
                {
                    "token": token,
                    "email": email,
                    "plan_tier": plan_tier,
                    "created_at": now,
                    "updated_at": now,
                    "active": True,
                },
            )
            conn.commit()
            logger.info("Created new user %s with plan %s", email, plan_tier)

    # Send license email
    send_license_email(email, token, plan_tier)
