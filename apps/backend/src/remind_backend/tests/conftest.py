"""Pytest configuration for backend tests."""

import os

import pytest


@pytest.fixture(scope="session", autouse=True)
def setup_env():
    """Set up environment variables for tests."""
    os.environ["GROQ_API_KEY"] = "gsk-test-key"
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
