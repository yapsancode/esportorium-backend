# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Esportorium is a FastAPI SaaS backend for **Mobile Legends Bang Bang (MLBB) tournaments in SEA**.
Organizers create and manage tournaments. Players register, join teams, and compete.
Target market: local SEA esports organizers (MY, ID, PH, TH, SG) currently using Challonge, Toornament, or manual methods.

## Stack

- **FastAPI** 0.128 + **Uvicorn** — ASGI server
- **SQLModel** 0.0.33 (built on SQLAlchemy 2.0 + Pydantic v2) — ORM and schema validation
- **PostgreSQL** via `psycopg2-binary`
- **python-dotenv** — environment variable loading
- **passlib[bcrypt]** — password hashing
- **python-jose[cryptography]** — JWT tokens
- **pydantic-settings** — environment variable validation

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
  main.py              # FastAPI app, lifespan, router registration
  core/
    config.py          # Settings via pydantic-settings, loaded from .env
    database.py        # SQLModel engine, session factory, get_session dependency
    security.py        # Password hashing, JWT creation/verification
    dependencies.py    # get_current_user, require_role(), require_min_role()
  models/              # SQLModel table models (DB schema)
    user.py            # User, UserRole enum, UserPlan enum
    tournament.py      # Tournament, TournamentStatus, TournamentFormat, SeriesFormat enums
    registration.py    # Registration, RegistrationStatus enum
    match.py           # Match (series), MatchStatus enum
    dispute.py         # Dispute, DisputeStatus enum
    team.py            # Team, TeamMember, TeamMemberRole enum
    game.py            # Game (single game within a match series)
    draft.py           # DraftEntry (hero picks/bans per game), DraftAction enum
  schemas/             # Pydantic request/response schemas (separate from DB models)
  api/                 # Route handlers, organized by resource
    auth.py            # /auth/* routes
    users.py           # /users/me route
    tournaments.py     # /tournaments/* routes (paginated, filterable)
    registrations.py   # /tournaments/{id}/register routes
    brackets.py        # /tournaments/{id}/bracket routes
    matches.py         # /matches/{id}/score routes
    disputes.py        # /disputes/* routes (paginated)
    games.py           # /matches/{id}/games routes
  services/            # Business logic layer
    auth.py            # User creation, login logic
    bracket.py         # Bracket generation, winner advancement
  tests/               # pytest test suite
```

## Key Design Patterns

- **SQLModel** is the single source of truth for ORM models (`table=True`) — keep DB models in `models/` and API schemas in `schemas/` to avoid tight coupling.
- **`get_session`** dependency uses `yield` to provide a session per request.
- **`core/config.py`** exposes a `Settings` class via `pydantic-settings` — all env vars validated at startup.
- **`core/dependencies.py`** contains all auth and role guards — always use these, never inline role checks in routes.
- All timestamps use `lambda: datetime.now(timezone.utc)` — never `datetime.utcnow()` (deprecated).
- All IDs are UUIDs using `default_factory=uuid.uuid4`.
- Soft deletes preferred over hard deletes where history matters (e.g. registrations).

---

"Schema migrations — SQLModel's create_all() only creates new tables, 
it never alters existing ones. When adding new columns to existing models, 
always provide the raw ALTER TABLE SQL alongside the model change so it 
can be run manually in pgAdmin during development. In production, use 
Alembic for migrations."

Also, for any future model changes in this codebase, always include 
the ALTER TABLE migration SQL in your response.

## Product Context

Esportorium is built specifically for **Mobile Legends Bang Bang (MLBB)** tournaments in SEA.
This is not a generic tournament platform — all features are designed around MLBB's game structure.

### Target Regions
MY, ID, PH, TH, SG

### User Roles (stored in users.role)
```
player → team_captain → organizer → moderator → admin → super_admin
```

### Plans (stored in users.plan)
```
free | pro | business | enterprise
```

### MLBB-Specific Structure
- **Teams:** 5 starters + 1 substitute. Player roles: roamer, gold, exp, mid, jungler, substitute (optional/flexible)
- **Match formats:** bo1, bo3, bo5 — matches are series, each containing individual games
- **Draft system:** Each game has hero picks and bans tracked per team per phase
- **Regions:** Tournaments and teams are tagged with SEA region codes

---

## What's Built

- [x] Auth — register, login, refresh, logout (JWT with role + plan in token)
- [x] Role guards — `get_current_user`, `require_role()`, `require_min_role()`
- [x] Tournament CRUD — organizer only, with role + plan enforcement
- [x] Player registration — join, withdraw (soft cancel), re-register
- [x] Bracket generation — single elimination, handles byes
- [x] Score reporting — per match, advances winner to next round
- [x] Disputes — raise, view, resolve, resets match for re-reporting
- [x] MLBB game + draft tracking — BO1/BO3/BO5 series, per-game results, hero pick/ban recording
- [x] Pagination + filtering — limit/offset on list endpoints, tournament filter by status/game/region
- [x] GET /users/me — returns current user's profile

## What's In Progress

- [ ] Team management endpoints
- [ ] Frontend (Next.js — separate repo)
- [ ] Billing (Stripe)
- [ ] Deployment

---

## Core Feature Loop (for reference)
1. ✅ Auth
2. ✅ Tournament CRUD
3. ✅ Player registration
4. ✅ Bracket generation
5. ✅ Score reporting
6. ✅ Disputes
7. ✅ MLBB-specific game + draft tracking