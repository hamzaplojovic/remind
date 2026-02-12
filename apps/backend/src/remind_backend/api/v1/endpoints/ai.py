"""AI suggestion endpoint."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from remind_backend.ai import suggest_reminder as ai_suggest_reminder
from remind_backend.auth import (
    authenticate_token,
    check_ai_quota,
    check_rate_limit,
    increment_rate_limit,
    log_usage,
)
from remind_backend.database import UserModel, get_db
from remind_backend.models import SuggestReminderRequest, SuggestReminderResponse

router = APIRouter()


@router.post("", response_model=SuggestReminderResponse)
async def suggest_reminder(
    request: SuggestReminderRequest,
    db: Session = Depends(get_db),
) -> SuggestReminderResponse:
    """Get AI-powered reminder suggestion."""
    try:
        user: UserModel = authenticate_token(db, request.license_token)
        check_rate_limit(db, user.id)
        check_ai_quota(db, user)

        ai_response = await ai_suggest_reminder(request.reminder_text)

        log_usage(
            db,
            user.id,
            ai_response["input_tokens"],
            ai_response["output_tokens"],
            ai_response["cost_cents"],
        )
        increment_rate_limit(db, user.id)

        return SuggestReminderResponse(
            suggested_text=ai_response["suggested_text"],
            priority=ai_response["priority"],
            due_time_suggestion=ai_response["due_time_suggestion"],
            cost_cents=ai_response["cost_cents"],
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI suggestion failed: {str(e)}")
