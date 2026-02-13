"""API v1 router combining all endpoints."""

from fastapi import APIRouter

from remind_backend.api.v1.endpoints import ai, checkout, health, usage

api_router = APIRouter()

# Health check endpoint
api_router.include_router(health.router, tags=["health"])

# AI suggestion endpoint
api_router.include_router(ai.router, prefix="/suggest-reminder", tags=["ai"])

# Usage stats endpoint
api_router.include_router(usage.router, prefix="/usage", tags=["usage"])

# Checkout endpoint (creates Polar checkout sessions)
api_router.include_router(checkout.router, prefix="/checkout", tags=["checkout"])
