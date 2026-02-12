"""Tests for FastAPI endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from remind_backend.main import app
from remind_backend.models import PriorityLevel


@pytest.fixture
def client():
    return TestClient(app)


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@patch("remind_backend.api.v1.endpoints.ai.get_db")
@patch("remind_backend.api.v1.endpoints.ai.authenticate_token")
def test_suggest_reminder_invalid_token(mock_auth, mock_get_db, client):
    """Test suggestion endpoint with invalid token."""
    from remind_backend.auth import AuthError

    mock_auth.side_effect = AuthError("Invalid license token")

    response = client.post(
        "/api/v1/suggest-reminder",
        json={
            "license_token": "invalid_token",
            "reminder_text": "call mom",
        },
    )
    assert response.status_code == 401
    assert "Invalid license" in response.json()["detail"]


@patch("remind_backend.api.v1.endpoints.ai.get_db")
@patch("remind_backend.api.v1.endpoints.ai.increment_rate_limit")
@patch("remind_backend.api.v1.endpoints.ai.log_usage")
@patch("remind_backend.api.v1.endpoints.ai.ai_suggest_reminder")
@patch("remind_backend.api.v1.endpoints.ai.check_ai_quota")
@patch("remind_backend.api.v1.endpoints.ai.check_rate_limit")
@patch("remind_backend.api.v1.endpoints.ai.authenticate_token")
def test_suggest_reminder_valid(
    mock_auth,
    mock_rate_limit,
    mock_quota,
    mock_suggest,
    mock_log,
    mock_increment,
    mock_get_db,
    client,
):
    """Test suggestion endpoint with valid token."""
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.plan_tier = "pro"
    mock_auth.return_value = mock_user
    mock_rate_limit.return_value = 9

    mock_suggest.return_value = {
        "suggested_text": "Call mom",
        "priority": PriorityLevel.HIGH,
        "due_time_suggestion": "tomorrow 3pm",
        "cost_cents": 1,
        "input_tokens": 20,
        "output_tokens": 10,
    }

    response = client.post(
        "/api/v1/suggest-reminder",
        json={
            "license_token": "test_token",
            "reminder_text": "call mom",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["suggested_text"] == "Call mom"
    assert data["priority"] == "high"
    assert data["cost_cents"] == 1


@patch("remind_backend.api.v1.endpoints.ai.get_db")
@patch("remind_backend.api.v1.endpoints.ai.check_ai_quota")
@patch("remind_backend.api.v1.endpoints.ai.check_rate_limit")
@patch("remind_backend.api.v1.endpoints.ai.authenticate_token")
def test_suggest_reminder_quota_exceeded(mock_auth, mock_rate_limit, mock_quota, mock_get_db, client):
    """Test suggestion endpoint with exhausted quota."""
    from remind_backend.auth import QuotaError

    mock_user = MagicMock()
    mock_user.id = 1
    mock_auth.return_value = mock_user
    mock_rate_limit.return_value = 9
    mock_quota.side_effect = QuotaError("Monthly AI quota exhausted")

    response = client.post(
        "/api/v1/suggest-reminder",
        json={
            "license_token": "test_token",
            "reminder_text": "call mom",
        },
    )
    assert response.status_code == 429
    assert "quota exhausted" in response.json()["detail"]


@patch("remind_backend.api.v1.endpoints.usage.get_db")
@patch("remind_backend.api.v1.endpoints.usage.authenticate_token")
def test_usage_stats_invalid_token(mock_auth, mock_get_db, client):
    """Test usage stats endpoint with invalid token."""
    from remind_backend.auth import AuthError

    mock_auth.side_effect = AuthError("Invalid license token")

    response = client.get("/api/v1/usage/stats?license_token=invalid_token")
    assert response.status_code == 401
    assert "Invalid license" in response.json()["detail"]


@patch("remind_backend.api.v1.endpoints.usage.get_db")
@patch("remind_backend.api.v1.endpoints.usage.get_usage_stats")
@patch("remind_backend.api.v1.endpoints.usage.authenticate_token")
def test_usage_stats_valid(mock_auth, mock_stats, mock_get_db, client):
    """Test usage stats endpoint with valid token."""
    mock_user = MagicMock()
    mock_user.id = 1
    mock_auth.return_value = mock_user

    mock_stats.return_value = {
        "user_id": 1,
        "plan_tier": "pro",
        "ai_quota_used": 0,
        "ai_quota_total": 1000,
        "ai_quota_remaining": 1000,
        "this_month_cost_cents": 0,
        "rate_limit_remaining": 10,
        "rate_limit_reset_at": "2025-01-30T12:05:00+00:00",
    }

    response = client.get("/api/v1/usage/stats?license_token=test_token")
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == 1
    assert data["plan_tier"] == "pro"
    assert data["ai_quota_total"] == 1000
