# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Esportorium is a FastAPI SaaS backend. The project is in early scaffolding — most files exist as stubs with placeholder comments.

## Stack

- **FastAPI** 0.128 + **Uvicorn** — ASGI server
- **SQLModel** 0.0.33 (built on SQLAlchemy 2.0 + Pydantic v2) — ORM and schema validation
- **PostgreSQL** via `psycopg2-binary`
- **python-dotenv** — environment variable loading

## Development Commands

Activate the virtual environment first:
```bash
source venv/Scripts/activate   # Windows bash
```

Install dependencies:
```bash
pip install -r requirements.txt
```

Run the development server:
```bash
uvicorn app.main:app --reload
```

Run tests:
```bash
pytest app/tests/
```

Run a single test file:
```bash
pytest app/tests/test_foo.py
```

## Architecture

```
app/
  main.py          # FastAPI app instantiation, router registration
  core/
    config.py      # Settings loaded from environment variables
    database.py    # SQLModel engine, session factory, get_session dependency
    security.py    # Password hashing and JWT creation/verification
  models/          # SQLModel table models (DB schema)
  schemas/         # Pydantic request/response schemas (separate from DB models)
  api/             # Route handlers, organized by resource
  services/        # Business logic layer between routers and DB
  tests/           # pytest test suite
```

### Key Design Patterns

- **SQLModel** is used as the single source of truth for both ORM models (`table=True`) and Pydantic validation schemas — keep DB models in `models/` and API-facing schemas in `schemas/` to avoid tight coupling.
- **`get_session`** dependency (to be defined in `core/database.py`) should use `yield` to provide a session per request.
- **`core/config.py`** should expose a `Settings` class using `pydantic-settings` (or `BaseSettings`) so all env vars are validated at startup.
- The project targets a multi-tenant SaaS structure — `organization.py` and `user.py` models are the foundational entities.

## Product Context

Esportorium is an esports tournament platform for SEA organizers.
Organizers create tournaments, players register and compete.

### User Roles (stored in users.role)
player → team_captain → organizer → moderator → admin → super_admin

### Plans (stored in users.plan)
free | pro | business | enterprise

### Core Feature Loop (build in this order)
1. Auth (register, login, refresh, logout)
2. Tournament CRUD
3. Player registration
4. Bracket generation
5. Score reporting
6. Disputes