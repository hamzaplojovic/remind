FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
RUN pip install uv

# Copy workspace files
COPY pyproject.toml .
COPY apps/backend ./apps/backend
COPY packages/shared ./packages/shared
COPY packages/database ./packages/database
COPY apps/backend/alembic ./alembic

# Install dependencies
RUN uv sync --frozen --no-dev

# Run migrations and start server
ENV PORT=8000
CMD ["sh", "-c", "cd /app && alembic upgrade head && uvicorn remind_backend.main:app --host 0.0.0.0 --port 8000"]
