"""Tests for AuthService."""

import pytest

from remind_shared import AuthenticationError
from remind_backend.services.auth_service import AuthService


class TestAuthService:
    """Tests for authentication service."""

    def test_authenticate_token_valid(self, test_session, test_user):
        """Test authenticating with a valid token."""
        service = AuthService(test_session)
        result = service.authenticate_token("remind_test_abc123")

        assert result["user_id"] == test_user.id
        assert result["token"] == "remind_test_abc123"
        assert result["email"] == "test@example.com"
        assert result["plan_tier"] == "pro"

    def test_authenticate_token_invalid_format(self, test_session):
        """Test authenticating with invalid token format."""
        service = AuthService(test_session)

        with pytest.raises(AuthenticationError, match="Invalid license token format"):
            service.authenticate_token("invalid_token")

    def test_authenticate_token_not_found(self, test_session):
        """Test authenticating with non-existent token."""
        service = AuthService(test_session)

        with pytest.raises(AuthenticationError, match="License token not found"):
            service.authenticate_token("remind_nonexistent_xyz789")

    def test_verify_token_valid(self, test_session, test_user):
        """Test verifying a valid token."""
        service = AuthService(test_session)
        assert service.verify_token("remind_test_abc123") is True

    def test_verify_token_invalid(self, test_session):
        """Test verifying an invalid token."""
        service = AuthService(test_session)
        assert service.verify_token("invalid") is False

    def test_verify_token_empty(self, test_session):
        """Test verifying an empty token."""
        service = AuthService(test_session)
        assert service.verify_token("") is False

    def test_get_user_plan_tier_pro(self, test_session, test_user):
        """Test getting pro plan tier."""
        service = AuthService(test_session)
        assert service.get_user_plan_tier("remind_test_abc123") == "pro"

    def test_get_user_plan_tier_default(self, test_session):
        """Test getting default (free) plan tier for non-existent token."""
        service = AuthService(test_session)
        assert service.get_user_plan_tier("remind_nonexistent") == "free"

    def test_get_or_create_user_existing(self, test_session, test_user):
        """Test getting an existing user."""
        service = AuthService(test_session)
        user = service.get_or_create_user("remind_test_abc123")

        assert user.id == test_user.id
        assert user.token == "remind_test_abc123"

    def test_get_or_create_user_new_pro(self, test_session):
        """Test creating a new pro user."""
        service = AuthService(test_session)
        user = service.get_or_create_user("remind_pro_xyz789", email="newuser@example.com")

        assert user.plan_tier == "pro"
        assert user.email == "newuser@example.com"
        assert user.token == "remind_pro_xyz789"

    def test_get_or_create_user_new_free(self, test_session):
        """Test creating a new free user."""
        service = AuthService(test_session)
        user = service.get_or_create_user("remind_free_abc123", email="free@example.com")

        assert user.plan_tier == "free"
        assert user.email == "free@example.com"

    def test_get_or_create_user_new_enterprise(self, test_session):
        """Test creating a new enterprise user."""
        service = AuthService(test_session)
        user = service.get_or_create_user("remind_enterprise_xyz", email="enterprise@example.com")

        assert user.plan_tier == "enterprise"
