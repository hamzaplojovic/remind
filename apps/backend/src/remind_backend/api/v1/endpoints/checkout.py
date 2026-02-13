"""Checkout endpoint — creates Polar checkout sessions and redirects."""

import logging

import httpx
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse

from remind_backend.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()

PLAN_TO_SETTING = {
    "free": "polar_product_free",
    "indie": "polar_product_indie",
    "pro": "polar_product_pro",
    "team": "polar_product_team",
}


@router.get("/{plan}")
async def create_checkout(
    plan: str,
    email: str | None = Query(None, description="Pre-fill customer email"),
):
    """Create a Polar checkout session and redirect the user.

    Used by both the web pricing buttons and the CLI register command.
    """
    settings = get_settings()

    if plan not in PLAN_TO_SETTING:
        raise HTTPException(status_code=400, detail=f"Invalid plan: {plan}")

    product_id = getattr(settings, PLAN_TO_SETTING[plan])
    if not product_id:
        raise HTTPException(status_code=500, detail=f"Product ID not configured for {plan}")

    if not settings.polar_api_key:
        raise HTTPException(status_code=500, detail="Polar API key not configured")

    # Create checkout session via Polar API
    payload: dict = {"products": [product_id]}
    if email:
        payload["customer_email"] = email

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.polar.sh/v1/checkouts/",
            json=payload,
            headers={
                "Authorization": f"Bearer {settings.polar_api_key}",
                "Content-Type": "application/json",
            },
            timeout=10,
        )

    if resp.status_code not in (200, 201):
        logger.error("Polar checkout creation failed: %s %s", resp.status_code, resp.text)
        raise HTTPException(status_code=502, detail="Failed to create checkout session")

    checkout_url = resp.json().get("url")
    if not checkout_url:
        raise HTTPException(status_code=502, detail="No checkout URL returned from Polar")

    return RedirectResponse(url=checkout_url, status_code=303)
