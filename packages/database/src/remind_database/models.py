"""SQLAlchemy ORM models for Remind database."""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String, Text, ForeignKey
from sqlalchemy.orm import declarative_base

from remind_shared import PriorityLevel, Reminder

Base = declarative_base()


class UserModel(Base):
    """SQLAlchemy ORM model for users."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    token = Column(String(255), nullable=False, unique=True, index=True)
    email = Column(String(255), nullable=True, index=True)
    plan_tier = Column(String(50), nullable=False, default="free")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class UsageLogModel(Base):
    """SQLAlchemy ORM model for API usage logs."""

    __tablename__ = "usage_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    input_tokens = Column(Integer, nullable=False)
    output_tokens = Column(Integer, nullable=False)
    cost_cents = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)


class RateLimitModel(Base):
    """SQLAlchemy ORM model for rate limiting."""

    __tablename__ = "rate_limits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    request_count = Column(Integer, nullable=False, default=0)
    reset_at = Column(DateTime(timezone=True), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class ReminderModel(Base):
    """SQLAlchemy ORM model for reminders."""

    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    text = Column(String(1000), nullable=False)
    due_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    done_at = Column(DateTime, nullable=True)
    priority = Column(String(20), nullable=False, default="medium")
    project_context = Column(String(500), nullable=True)
    ai_suggested_text = Column(Text, nullable=True)

    def to_pydantic(self) -> Reminder:
        """Convert ORM model to Pydantic model."""
        return Reminder(
            id=self.id,
            text=self.text,
            due_at=self.due_at,
            created_at=self.created_at,
            done_at=self.done_at,
            priority=PriorityLevel(self.priority),
            project_context=self.project_context,
            ai_suggested_text=self.ai_suggested_text,
        )
