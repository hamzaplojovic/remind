"""Pytest configuration and fixtures for CLI tests."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from remind_database.models import Base, ReminderModel


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
