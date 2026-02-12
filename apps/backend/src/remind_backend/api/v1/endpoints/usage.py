"""Usage statistics endpoint."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from remind_backend.auth import authenticate_token, get_usage_stats
from remind_backend.database import get_db
from remind_backend.models import UsageStats

router = APIRouter()


@router.get("/stats", response_model=UsageStats)
async def usage_stats(
    license_token: str = Query(...),
    db: Session = Depends(get_db),
) -> UsageStats:
    """Get usage statistics for the user."""
    user = authenticate_token(db, license_token)
    stats = get_usage_stats(db, user)
    return UsageStats(**stats)
