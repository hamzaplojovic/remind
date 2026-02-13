"""Polar webhook handler for processing payments and creating users."""

import logging
import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Request, HTTPException
from sqlalchemy import text
from polar_sdk.webhooks import validate_event, WebhookVerificationError

from remind_backend.config import get_settings
from remind_backend.database import get_engine
from remind_backend.email import send_license_email

logger = logging.getLogger(__name__)
router = APIRouter()


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


@router.post("/polar")
async def polar_webhook(request: Request):
    """Handle Polar payment webhooks.

    Uses polar_sdk.webhooks.validate_event for Standard Webhooks signature verification.
    """
    settings = get_settings()
    body = await request.body()

    # Validate webhook signature using Polar SDK
    try:
        event = validate_event(
            body=body,
            headers=dict(request.headers),
            secret=settings.polar_webhook_secret,
        )
    except WebhookVerificationError as e:
        logger.warning("Invalid webhook signature: %s", e)
        raise HTTPException(status_code=403, detail="Invalid signature")

    event_type = event.type if hasattr(event, "type") else str(event.get("type", ""))

    logger.info("Polar webhook received: %s", event_type)

    if event_type in ("order.created", "order.paid", "subscription.created"):
        event_data = event.data if hasattr(event, "data") else event.get("data", {})
        await _handle_order(event_data)
    elif event_type == "checkout.updated":
        event_data = event.data if hasattr(event, "data") else event.get("data", {})
        status = getattr(event_data, "status", None) or event_data.get("status", "")
        if status == "succeeded":
            await _handle_checkout(event_data)
    else:
        logger.info("Ignoring event type: %s", event_type)

    return {"status": "ok"}


async def _handle_checkout(data):
    """Process a completed checkout — extract email and product, delegate to _handle_order."""
    if hasattr(data, "customer_email"):
        email = data.customer_email
    else:
        email = data.get("customer_email") or data.get("customer", {}).get("email")

    if hasattr(data, "product"):
        product = data.product
        product_id = getattr(product, "id", "")
    elif hasattr(data, "product_id"):
        product_id = data.product_id
    else:
        product_id = data.get("product_id", "") or data.get("product", {}).get("id", "")

    if not email:
        logger.error("No email in checkout payload: %s", data)
        return

    # Build a minimal dict that _handle_order understands
    await _handle_order({
        "customer": {"email": email},
        "product": {"id": product_id},
    })


async def _handle_order(data):
    """Process a completed order — create user and email token."""
    # Extract customer info — data may be a Pydantic model or dict
    if hasattr(data, "customer"):
        customer = data.customer
        email = getattr(customer, "email", None)
        product = data.product
        product_id = getattr(product, "id", "")
    else:
        customer = data.get("customer", {})
        email = customer.get("email") or data.get("customer_email")
        product = data.get("product", {})
        product_id = product.get("id", "")

    if not email:
        logger.error("No email in webhook payload: %s", data)
        return

    tier_map = _get_product_tier_map()
    plan_tier = tier_map.get(str(product_id), "free")

    logger.info("Creating user: email=%s plan=%s product_id=%s", email, plan_tier, product_id)

    token = _generate_token(plan_tier)
    now = datetime.now(timezone.utc)
    engine = get_engine()

    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT id, token, plan_tier FROM users WHERE email = :email"),
            {"email": email},
        )
        existing = result.fetchone()

        if existing:
            conn.execute(
                text(
                    "UPDATE users SET plan_tier = :plan_tier, active = true, updated_at = :now "
                    "WHERE email = :email"
                ),
                {"plan_tier": plan_tier, "now": now, "email": email},
            )
            conn.commit()
            token = existing.token
            logger.info("Upgraded existing user %s to %s", email, plan_tier)
        else:
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

    send_license_email(email, token, plan_tier)
