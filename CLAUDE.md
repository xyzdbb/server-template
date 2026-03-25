# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Development server
uv run uvicorn app.main:app --reload

# Testing
uv run pytest                                          # All tests with coverage
uv run pytest tests/api/v1/test_auth.py               # Single module
uv run pytest tests/api/v1/test_auth.py::test_login   # Single test

# Linting & formatting
uv run ruff check .
uv run ruff format .
uv run mypy app

# Database migrations
uv run alembic revision --autogenerate -m "describe change"
uv run alembic upgrade head
uv run alembic downgrade -1

# Docker (dev with hot reload, prod with gunicorn)
docker compose --profile dev up -d
docker compose --profile prod up -d
docker compose exec backend-dev alembic upgrade head
docker compose exec backend-dev python scripts/bootstrap_db.py
```

## Architecture

This is a production-ready FastAPI backend template using PostgreSQL, Redis, and JWT authentication.

### Four-Layer Structure

Each business module in `app/modules/<name>/` follows this pattern:
- **Endpoint** (`endpoints/`) — HTTP handlers, request/response serialization
- **Service** (`service.py`) — Business logic, permission checks, Redis ops
- **Repository** (`repository.py`) — Data access via `RepositoryBase[ModelType]`
- **Model** (`models.py`) — SQLModel ORM definitions (auto-discovered by Alembic)

### Key Conventions

- **Soft delete**: All models inherit `TableBase` (`app/models/base.py`) which adds `id`, `created_at`, `updated_at`, `deleted_at`. Queries automatically filter soft-deleted records.
- **Repository pattern**: `RepositoryBase` in `app/repositories/base.py` provides generic CRUD. Extend it per module.
- **Dependency injection**: `app/api/deps.py` exports `SessionDep`, `CurrentUser`, `TokenDep` for use in endpoints.
- **Exceptions**: Raise `AppException` subclasses from `app/utils/exceptions.py`; the error handler middleware converts them to JSON.
- **Transactions**: Use `commit_and_refresh()` from `app/core/transaction.py` after mutations.
- **Line length**: 120 characters (ruff).

### Authentication

JWT dual-token system: access tokens (30 min) + refresh tokens (7 days). Refresh token revocation uses Redis jti tracking. Superuser access via `is_superuser` boolean on User model.

### Middleware Chain (LIFO — last added = first executed)

1. ProxyHeadersMiddleware — extract real client IP
2. RequestIDMiddleware — generate UUID, inject `X-Request-Id`
3. SecurityHeadersMiddleware — security response headers
4. LoggingMiddleware — structured JSON request logs
5. CORSMiddleware
6. ErrorHandler — `AppException` → JSON response

### Adding a New Module

1. Create `app/modules/<name>/` with `models.py`, `repository.py`, `service.py`, `endpoints/`
2. Register router in `app/api/v1/router.py`
3. Generate migration: `uv run alembic revision --autogenerate -m "add <name>"`

### Environment Variables

Copy `.env.example` to `.env`. Required: `SECRET_KEY` (min 32 chars), `POSTGRES_*`, `REDIS_URL`, `FIRST_SUPERUSER*`. See `app/core/config.py` for all settings.
