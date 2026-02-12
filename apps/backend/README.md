# Remind Backend API

FastAPI-based backend server for the Remind system.

## Quick Start

```bash
uv sync
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/remind
alembic upgrade head
uv run uvicorn remind_backend.main:app --reload
```

## API Endpoints

- `GET /health` - Health check
- `POST /api/v1/suggest-reminder` - Get AI suggestion for reminder
- `GET /api/v1/usage-stats` - Get user usage statistics
- `POST /webhooks/polar` - License webhook handler

## Configuration

Environment variables:
- `DATABASE_URL` - PostgreSQL connection string
- `OPENAI_API_KEY` - OpenAI API key for AI features
- `CORS_ORIGINS` - Comma-separated list of CORS origins

## Development

```bash
# Run tests
pytest tests -v --cov

# Run migrations
alembic upgrade head

# Type checking
mypy src --strict

# Linting
ruff check src
```

## Documentation

See [../../REFACTORING_COMPLETE.md](../../REFACTORING_COMPLETE.md) for architecture and API details.
