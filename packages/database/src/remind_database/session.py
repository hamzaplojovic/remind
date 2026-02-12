"""Database session and engine management."""

import os
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool, QueuePool, StaticPool

from remind_database.models import Base


class DatabaseConfig:
    """Database configuration."""

    def __init__(self, database_url: str | None = None, db_path: Path | None = None):
        """Initialize database configuration.

        Args:
            database_url: Full database URL (e.g., postgresql://user:pass@localhost/db)
                         If not provided, falls back to SQLite at db_path
            db_path: Path to SQLite database file (only used if database_url not provided)
        """
        if database_url:
            self.url = database_url
        elif db_path:
            self.url = f"sqlite:///{db_path}"
        else:
            # Default to local SQLite
            default_path = Path.home() / ".remind" / "remind.db"
            self.url = f"sqlite:///{default_path}"

    def is_postgres(self) -> bool:
        """Check if this is a PostgreSQL database."""
        return self.url.startswith("postgresql://") or self.url.startswith("postgres://")

    def is_sqlite(self) -> bool:
        """Check if this is a SQLite database."""
        return self.url.startswith("sqlite://")


class DatabaseSession:
    """Database session manager supporting SQLite and PostgreSQL."""

    _instance: "DatabaseSession | None" = None
    _engine = None
    _session_factory = None

    def __new__(cls, config: DatabaseConfig | None = None):
        """Singleton pattern for database session."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            if config:
                cls._instance._init(config)
        return cls._instance

    def _init(self, config: DatabaseConfig) -> None:
        """Initialize database engine and session factory."""
        self.config = config

        # Configure engine based on database type
        if config.is_postgres():
            # PostgreSQL production configuration
            DatabaseSession._engine = create_engine(
                config.url,
                poolclass=QueuePool,
                pool_size=20,
                max_overflow=40,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=os.getenv("DATABASE_ECHO", "false").lower() == "true",
            )
        elif config.is_sqlite():
            # SQLite development configuration
            db_path = config.url.replace("sqlite:///", "")

            # For in-memory testing
            if db_path == ":memory:":
                DatabaseSession._engine = create_engine(
                    "sqlite:///:memory:",
                    connect_args={"check_same_thread": False},
                    poolclass=StaticPool,
                )
            else:
                # Ensure directory exists
                Path(db_path).parent.mkdir(parents=True, exist_ok=True)
                DatabaseSession._engine = create_engine(
                    config.url,
                    connect_args={"check_same_thread": False},
                    poolclass=NullPool,
                )

        DatabaseSession._session_factory = sessionmaker(
            bind=DatabaseSession._engine,
            expire_on_commit=False,
        )

        # Create tables
        Base.metadata.create_all(DatabaseSession._engine)

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Context manager for database sessions."""
        if DatabaseSession._session_factory is None:
            raise RuntimeError("DatabaseSession not initialized. Call DatabaseSession(config) first.")

        session = DatabaseSession._session_factory()
        try:
            yield session
        finally:
            session.close()

    def close(self) -> None:
        """Close the database connection."""
        if DatabaseSession._engine:
            DatabaseSession._engine.dispose()
            DatabaseSession._engine = None
            DatabaseSession._session_factory = None

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton instance (useful for testing)."""
        if cls._instance:
            cls._instance.close()
        cls._instance = None
        cls._engine = None
        cls._session_factory = None
