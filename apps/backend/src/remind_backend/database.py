"""Database models and session management."""

from datetime import datetime, timezone
from typing import Generator

from sqlalchemy import ForeignKey, String, create_engine
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    sessionmaker,
)
from sqlalchemy.types import JSON


class Base(DeclarativeBase):
    pass


class UserModel(Base):
    """Represents a user with a license token."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    token: Mapped[str] = mapped_column(String, unique=True, index=True)
    email: Mapped[str] = mapped_column(String)
    plan_tier: Mapped[str] = mapped_column(String)  # free, indie, pro, team
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
    )
    expires_at: Mapped[datetime | None] = mapped_column(default=None)
    active: Mapped[bool] = mapped_column(default=True)

    def __repr__(self) -> str:
        return f"<UserModel token={self.token} plan={self.plan_tier}>"


class UsageLogModel(Base):
    """Tracks usage of features for billing."""

    __tablename__ = "usage_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    feature: Mapped[str] = mapped_column(String)  # "ai_suggestion", "nudge", etc.
    timestamp: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
    )
    input_tokens: Mapped[int] = mapped_column(default=0)
    output_tokens: Mapped[int] = mapped_column(default=0)
    cost_cents: Mapped[int] = mapped_column()  # Store as cents (integer)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)

    def __repr__(self) -> str:
        return f"<UsageLogModel user_id={self.user_id} feature={self.feature} cost={self.cost_cents}¢>"


class RateLimitModel(Base):
    """Tracks request rate limiting per user."""

    __tablename__ = "rate_limits"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    request_count: Mapped[int] = mapped_column(default=0)
    reset_at: Mapped[datetime] = mapped_column()

    def __repr__(self) -> str:
        return f"<RateLimitModel user_id={self.user_id} count={self.request_count}>"


# Database session management
_engine = None
_session_local = None


def get_engine():
    """Get or create database engine (singleton pattern)."""
    global _engine
    if _engine is None:
        from remind_backend.config import get_settings

        settings = get_settings()
        is_sqlite = "sqlite" in settings.database_url
        connect_args = {"check_same_thread": False} if is_sqlite else {}

        pool_kwargs = {}
        if not is_sqlite:
            pool_kwargs = {
                "pool_size": 10,
                "max_overflow": 20,
                "pool_pre_ping": True,
                "pool_recycle": 3600,
            }

        _engine = create_engine(
            settings.database_url,
            connect_args=connect_args,
            **pool_kwargs,
        )
    return _engine


def get_session_local():
    """Get or create session factory (singleton pattern)."""
    global _session_local
    if _session_local is None:
        _session_local = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=get_engine(),
        )
    return _session_local


def get_db() -> Generator[Session, None, None]:
    """Get database session (for dependency injection)."""
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
