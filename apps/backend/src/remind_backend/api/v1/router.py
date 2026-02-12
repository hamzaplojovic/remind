"""API v1 router combining all endpoints."""

from fastapi import APIRouter

from remind_backend.api.v1.endpoints import ai, health, usage

api_router = APIRouter()

# Health check endpoint
api_router.include_router(health.router, tags=["health"])

# AI suggestion endpoint
api_router.include_router(ai.router, prefix="/suggest-reminder", tags=["ai"])

# Usage stats endpoint
api_router.include_router(usage.router, prefix="/usage", tags=["usage"])

# Webhook endpoints (separate from v1)
# Note: Webhooks are at /webhooks/, not /api/v1/webhooks/
