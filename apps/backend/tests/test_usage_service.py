"""Tests for UsageService."""

from datetime import datetime, timezone

import pytest

from remind_shared import ValidationError
from remind_backend.services.usage_service import UsageService
from remind_database.models import UsageLogModel


class TestUsageService:
    """Tests for usage tracking service."""

    def test_check_rate_limit_first_request(self, test_session, test_user):
        """Test first request within rate limit."""
        service = UsageService(test_session)
        assert service.check_rate_limit(test_user.id) is True

    def test_check_rate_limit_multiple_requests(self, test_session, test_user):
        """Test multiple requests within rate limit."""
        service = UsageService(test_session)

        for _ in range(10):
            assert service.check_rate_limit(test_user.id) is True

    def test_check_rate_limit_exceeded(self, test_session, test_user):
        """Test rate limit exceeded."""
        service = UsageService(test_session)

        # Make 10 requests (at limit)
        for _ in range(10):
            service.check_rate_limit(test_user.id)

        # 11th request should be rejected
        assert service.check_rate_limit(test_user.id) is False

    def test_check_ai_quota_free_plan(self, test_session, test_user):
        """Test AI quota check for free plan."""
        test_user.plan_tier = "free"
        test_session.commit()

        service = UsageService(test_session)
        assert service.check_ai_quota(test_user.id, "free") is True

    def test_check_ai_quota_pro_plan(self, test_session, test_user):
        """Test AI quota check for pro plan."""
        service = UsageService(test_session)
        assert service.check_ai_quota(test_user.id, "pro") is True

    def test_check_ai_quota_enterprise_unlimited(self, test_session, test_user):
        """Test AI quota check for enterprise (unlimited)."""
        service = UsageService(test_session)
        assert service.check_ai_quota(test_user.id, "enterprise") is True

    def test_check_ai_quota_exceeded(self, test_session, test_user):
        """Test AI quota exceeded for free plan."""
        test_user.plan_tier = "free"
        test_session.commit()

        service = UsageService(test_session)

        # Log usage exceeding free quota (100 tokens)
        for _ in range(200):
            service.log_usage(test_user.id, 1, 1, 1)

        with pytest.raises(ValidationError, match="AI quota exceeded"):
            service.check_ai_quota(test_user.id, "free")

    def test_log_usage(self, test_session, test_user):
        """Test logging usage."""
        service = UsageService(test_session)
        service.log_usage(test_user.id, 100, 50, 5)

        # Verify logged
        logs = test_session.query(UsageLogModel).filter_by(user_id=test_user.id).all()
        assert len(logs) == 1
        assert logs[0].input_tokens == 100
        assert logs[0].output_tokens == 50
        assert logs[0].cost_cents == 5

    def test_get_usage_stats_no_usage(self, test_session, test_user):
        """Test getting stats with no usage."""
        service = UsageService(test_session)
        stats = service.get_usage_stats(test_user.id)

        assert stats["user_id"] == test_user.id
        assert stats["plan_tier"] == "pro"
        assert stats["ai_quota_used"] == 0
        assert stats["ai_quota_total"] == 1000
        assert stats["ai_quota_remaining"] == 1000
        assert stats["this_month_cost_cents"] == 0

    def test_get_usage_stats_with_usage(self, test_session, test_user):
        """Test getting stats with usage logged."""
        service = UsageService(test_session)
        service.log_usage(test_user.id, 100, 50, 5)
        service.log_usage(test_user.id, 100, 50, 5)

        stats = service.get_usage_stats(test_user.id)

        assert stats["ai_quota_used"] == 100  # 50 + 50
        assert stats["ai_quota_remaining"] == 900
        assert stats["this_month_cost_cents"] == 10  # 5 + 5

    def test_get_usage_stats_user_not_found(self, test_session):
        """Test getting stats for non-existent user."""
        service = UsageService(test_session)

        with pytest.raises(ValidationError, match="User .* not found"):
            service.get_usage_stats(999)

    def test_increment_rate_limit(self, test_session, test_user):
        """Test incrementing rate limit counter."""
        service = UsageService(test_session)

        # Initial increment
        service.increment_rate_limit(test_user.id)

        # Verify it was incremented
        stats = service.get_usage_stats(test_user.id)
        assert stats["rate_limit_remaining"] == 9  # 10 - 1
