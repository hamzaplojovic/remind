"""Tests for authentication and authorization."""

from datetime import datetime, timezone, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from remind_backend.database import Base, UserModel, UsageLogModel
from remind_backend.auth import (
    authenticate_token,
    check_rate_limit,
    check_ai_quota,
    get_monthly_quota_used,
    increment_rate_limit,
    AuthError,
    QuotaError,
)


@pytest.fixture
def test_db():
    """Create in-memory test database."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False)
    db = SessionLocal()
    yield db
    db.close()


def test_authenticate_token_valid(test_db):
    """Test authenticating with valid token."""
    user = UserModel(
        token="test_token_123",
        email="user@example.com",
        plan_tier="pro",
        active=True,
    )
    test_db.add(user)
    test_db.commit()

    authenticated_user = authenticate_token(test_db, "test_token_123")
    assert authenticated_user.id == user.id
    assert authenticated_user.plan_tier == "pro"


def test_authenticate_token_invalid(test_db):
    """Test authentication fails with invalid token."""
    with pytest.raises(AuthError):
        authenticate_token(test_db, "invalid_token")


def test_authenticate_token_inactive(test_db):
    """Test authentication fails with inactive user."""
    user = UserModel(
        token="test_token_123",
        email="user@example.com",
        plan_tier="pro",
        active=False,
    )
    test_db.add(user)
    test_db.commit()

    with pytest.raises(AuthError, match="inactive"):
        authenticate_token(test_db, "test_token_123")


def test_check_rate_limit_first_request(test_db):
    """Test rate limit resets on first request of window."""
    user = UserModel(token="test", email="test@example.com", plan_tier="pro", active=True)
    test_db.add(user)
    test_db.commit()

    remaining = check_rate_limit(test_db, user.id)
    assert remaining == 9  # 10 - 1 (this request)


def test_check_rate_limit_exceeds(test_db):
    """Test rate limit exceeded raises error."""
    user = UserModel(token="test", email="test@example.com", plan_tier="pro", active=True)
    test_db.add(user)
    test_db.commit()

    for _ in range(10):
        check_rate_limit(test_db, user.id)
        increment_rate_limit(test_db, user.id)

    with pytest.raises(QuotaError, match="Rate limit exceeded"):
        check_rate_limit(test_db, user.id)


def test_get_monthly_quota_used(test_db):
    """Test calculating monthly quota used."""
    user = UserModel(token="test", email="test@example.com", plan_tier="pro", active=True)
    test_db.add(user)
    test_db.commit()

    for _ in range(3):
        log = UsageLogModel(
            user_id=user.id,
            input_tokens=100,
            output_tokens=50,
            cost_cents=1,
        )
        test_db.add(log)
    test_db.commit()

    used = get_monthly_quota_used(test_db, user.id)
    assert used == 3


def test_check_ai_quota_free_plan(test_db):
    """Test free plan has limited AI quota."""
    user = UserModel(token="test", email="test@example.com", plan_tier="free", active=True)
    test_db.add(user)
    test_db.commit()

    for _ in range(5):
        log = UsageLogModel(
            user_id=user.id,
            input_tokens=100,
            output_tokens=50,
            cost_cents=1,
        )
        test_db.add(log)
    test_db.commit()

    with pytest.raises(QuotaError, match="quota exhausted"):
        check_ai_quota(test_db, user)


def test_check_ai_quota_pro_plan_available(test_db):
    """Test pro plan has higher quota."""
    user = UserModel(token="test", email="test@example.com", plan_tier="pro", active=True)
    test_db.add(user)
    test_db.commit()

    for _ in range(100):
        log = UsageLogModel(
            user_id=user.id,
            input_tokens=100,
            output_tokens=50,
            cost_cents=1,
        )
        test_db.add(log)
    test_db.commit()

    check_ai_quota(test_db, user)  # Should not raise
