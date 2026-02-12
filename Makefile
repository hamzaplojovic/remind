.PHONY: help install test test-cli test-backend lint format clean dev-cli dev-backend dev-all migrate-cli migrate-backend docker-up docker-down

help:
	@echo "Remind Monorepo - Available commands:"
	@echo ""
	@echo "Development:"
	@echo "  make install          Install all dependencies"
	@echo "  make dev-cli          Run CLI in development mode"
	@echo "  make dev-backend      Run backend in development mode"
	@echo "  make dev-all          Run both CLI and backend (requires tmux)"
	@echo ""
	@echo "Testing:"
	@echo "  make test             Run all tests with coverage"
	@echo "  make test-cli         Run CLI tests only"
	@echo "  make test-backend     Run backend tests only"
	@echo ""
	@echo "Database:"
	@echo "  make migrate-cli      Run CLI database migrations"
	@echo "  make migrate-backend  Run backend database migrations"
	@echo "  make reset-db         Drop and recreate all databases"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint             Run linting (ruff + mypy)"
	@echo "  make format           Format code (ruff)"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-up        Start services (backend + postgres)"
	@echo "  make docker-down      Stop services"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean            Remove build artifacts and caches"

install:
	uv sync --all-extras

dev-cli:
	cd apps/cli && uv run remind --help

dev-backend:
	cd apps/backend/src/remind_backend && uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

dev-all:
	@echo "Starting CLI and backend (requires tmux)"
	@tmux new-session -d -s remind -x 200 -y 50
	@tmux send-keys -t remind "cd /Users/hamzaplojovic/Documents/remind-monorepo && make dev-cli" Enter
	@tmux split-window -t remind -h
	@tmux send-keys -t remind "cd /Users/hamzaplojovic/Documents/remind-monorepo && make dev-backend" Enter
	@tmux attach -t remind

test:
	pytest apps/ packages/ -v --cov=apps --cov=packages --cov-report=html

test-cli:
	pytest apps/cli -v --cov=apps/cli

test-backend:
	pytest apps/backend -v --cov=apps/backend

lint:
	ruff check apps/ packages/
	mypy apps/ packages/ --ignore-missing-imports

format:
	ruff format apps/ packages/

migrate-cli:
	cd packages/database && alembic upgrade head

migrate-backend:
	cd apps/backend && alembic upgrade head

reset-db:
	rm -f apps/cli/src/remind_cli/*.db
	rm -f apps/cli/src/remind_cli/*.db-wal
	rm -f apps/cli/src/remind_cli/*.db-shm
	$(MAKE) migrate-cli
	$(MAKE) migrate-backend

docker-up:
	docker-compose -f infrastructure/docker/docker-compose.yml up -d

docker-down:
	docker-compose -f infrastructure/docker/docker-compose.yml down

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .coverage htmlcov dist build *.egg-info
	rm -rf apps/backend/.pytest_cache apps/cli/.pytest_cache
