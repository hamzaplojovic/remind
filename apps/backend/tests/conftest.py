"""Pytest configuration and fixtures for backend tests."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from remind_database.models import Base, UserModel


@pytest.fixture
def test_db_engine():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture
def test_session(test_db_engine):
    """Create a test database session."""
    SessionLocal = sessionmaker(bind=test_db_engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def test_user(test_session) -> UserModel:
    """Create a test user."""
    user = UserModel(
        token="remind_test_abc123",
        email="test@example.com",
        plan_tier="pro",
    )
    test_session.add(user)
    test_session.commit()
    test_session.refresh(user)
    return user
