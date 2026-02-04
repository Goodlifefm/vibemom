# Project Map (vibe-market)

## How to run
- Dev (local, Windows shown):
  - `python -m venv .venv`
  - `.venv\Scripts\activate`
  - `pip install -r requirements.txt`
  - `cp .env.example .env`
  - `alembic upgrade head`
  - `python main.py`
- Build/Run (Docker):
  - `cp .env.example .env`
  - `docker compose up --build`
  - `docker compose up -d --build`
  - `AUTO_MIGRATE=true` (default). Set `AUTO_MIGRATE=false` to skip startup migrations.
  - `APP_ENV=production` disables startup migrations regardless of `AUTO_MIGRATE`.
  - Explicit migrations: `docker compose run --rm bot alembic upgrade head`
- Tests:
  - `pytest`
  - `python -m pytest tests/ -v`
- Useful scripts:
  - `python scripts/audit_copy.py`
  - `python scripts/test_feed.py`
  - `python scripts/test_feed.py --dry-run`
  - `python -m src.bot.health`

## Architecture overview
- `main.py`: app entrypoint; loads `Settings`, initializes DB session factory, starts aiogram polling.
- `src/bot/`: V1 bot implementation.
  - `handlers/`: command routing (`/start`, `/submit`, `/request`, `/catalog`, `/leads`, `/admin`).
  - `services/`: business logic around users, projects, leads, matching.
  - `database/`: SQLAlchemy models and async session wiring.
  - `messages.py`, `keyboards.py`, `renderer.py`: UX text, keyboards, rendering.
- `src/v2/`: V2 UX flow and moderation.
  - `routers/`: menu/start/form/preview/moderation/fallback.
  - `fsm/`: step definitions and states.
  - `repo/`: submission/admin/user data access.
  - `rendering/`: project rendering for V2.
- `src/utils/`: shared text helpers.
- `alembic/` + `alembic.ini`: migrations.
- `tests/`: pytest suite for schemas, rendering, services, V2.
- `scripts/`: utilities (copy audit, feed test, V2 repo smoke).
- `docker-compose.yml` + `Dockerfile`: runtime stack (bot + Postgres).
- `.github/workflows/deploy.yml`: auto-deploy to VPS on push.

## Env vars / configs
From `.env.example` and compose:
- Required:
  - `BOT_TOKEN`
  - `DATABASE_URL`
- Optional:
  - `ADMIN_CHAT_ID`
  - `FEED_CHAT_ID`
  - `ADMIN_IDS`
  - `ADMIN_TELEGRAM_IDS`
  - `LOG_LEVEL`
  - `APP_ENV`
  - `AUTO_MIGRATE`
  - `V2_ENABLED`
  - `V2_CANARY_MODE`
  - `V2_ALLOWLIST`
- Docker-only (compose default):
  - `POSTGRES_PASSWORD`
- GitHub Actions secrets (deploy):
  - `VPS_HOST`
  - `VPS_USER`
  - `VPS_SSH_KEY`
  - `VPS_PORT` (optional)

## External services
- Telegram Bot API (aiogram).
- PostgreSQL database (local or Docker).
- GitHub Actions + SSH to VPS for deploy.

## Top risks / tech debt (actionable)
1. No explicit dev/run script or Makefile: hard to standardize local workflow. Add `Makefile` or `scripts/dev.ps1`.
2. V1/V2 routing is runtime-flagged without smoke test gating; risk of regressions. Add CI job that runs V1/V2 flow smoke tests.
3. Startup migrations are now env-gated; ensure production sets `AUTO_MIGRATE=false` and runs migrations explicitly.
4. `.env` exists in repo root: risk of accidental commit/secrets drift. Ensure `.env` is in `.gitignore` and avoid storing real tokens.
5. No health/readiness endpoint for the bot outside `python -m src.bot.health`. Consider exposing a simple HTTP healthcheck or expanding health script for CI.
6. Settings validation is minimal (only `BOT_TOKEN` is required). Add stricter validation for `DATABASE_URL` and admin IDs.
7. DB session factory is global; no explicit shutdown/cleanup. Add graceful shutdown hook to close engine.
8. Logs are structured but `LOG_LEVEL` is unused in `main.py`. Wire `LOG_LEVEL` into `logging.basicConfig`.
9. No CI for tests/lint visible (only deploy workflow). Add GitHub Actions workflow for `pytest` and ruff/black.
10. V2 data models and V1 models coexist; migration/compat rules are implicit. Add docs or integration tests to ensure data consistency.
