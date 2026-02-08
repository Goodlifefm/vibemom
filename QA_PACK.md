# QA Pack — VPS Commands & Expected Output

## Step 1: Diagnosis — what can break bot runtime

**What can break**

| Cause | Symptom | Fix |
|-------|--------|-----|
| **Wrong folder** | `docker compose` fails: "no configuration file" or "Cannot find file .env" | Run from project root where `docker-compose.yml` and `.env` exist (e.g. `/root/vibemom`). |
| **Missing/empty BOT_TOKEN** | Bot exits immediately: `TokenValidationError: Token is invalid!` | Set valid `BOT_TOKEN=...` in `.env` (from @BotFather). |
| **No .env** | Env vars empty; token validation or DB connection fails | Copy `.env.example` to `.env` and fill `BOT_TOKEN`, optionally `ADMIN_CHAT_ID`, `ADMIN_TELEGRAM_IDS`. |
| **DATABASE_URL wrong** | DB init or first request fails (e.g. connection refused) | In Docker, `DATABASE_URL` is overridden by compose to `postgresql+asyncpg://postgres:postgres@db:5432/vibe_market`. Do not point to `localhost` inside the bot container — use host `db`. |
| **ADMIN_CHAT_ID empty** | Moderation still works; submissions just don’t get sent to a group | Optional. To enable: set `ADMIN_CHAT_ID=-1001234567890` in `.env` and add the bot to that group. |
| **`InvalidPasswordError: password authentication failed for user "postgres"`** | DB was initialized with a different password than the one the bot uses | Either set `POSTGRES_PASSWORD=` in `.env` to the password the DB was created with, or **reset the DB volume** so Postgres re-initializes with the password from compose: `docker compose down -v` then `docker compose up -d --build`. |

**Config loading:** `Settings()` (pydantic-settings) reads from **environment variables** first. Compose injects vars from `env_file: .env` and from the `environment:` block. So `BOT_TOKEN`, `DATABASE_URL`, `ADMIN_CHAT_ID`, `ADMIN_TELEGRAM_IDS`, `V2_ENABLED` from `.env` are available in the bot container.

**Exact commands to verify status**

**On VPS (from project root, e.g. `/root/vibemom`):**

```bash
# 1. Go to project root (folder with docker-compose.yml and .env)
cd /root/vibemom

# 2. Check files present
ls -la docker-compose.yml .env

# 3. Build and start (detached)
docker compose up -d --build

# 4. Check bot logs (errors appear here)
docker compose logs bot --tail=100

# 5. If bot exited, see exit reason
docker compose ps -a
```

**Verify .env is loaded (inside container):**

```bash
docker compose exec -T bot env | grep -E 'BOT_TOKEN|DATABASE_URL|ADMIN_CHAT_ID'
```

(You should see `BOT_TOKEN=...`, `DATABASE_URL=postgresql+asyncpg://...@db:...`, and `ADMIN_CHAT_ID=...` if set. Token value may be redacted in logs.)

**Locally (no Docker):**

```bash
cd /path/to/vibe-market
cp .env.example .env
# Edit .env: set BOT_TOKEN, optionally ADMIN_CHAT_ID
python -c "from src.bot.config import Settings; s=Settings(); print('OK' if s.bot_token else 'BOT_TOKEN empty')"
```

---

## 1. Exact terminal commands (max 5)

Run these **on the VPS** from the project root (e.g. `/root/vibemom` or `/root/vibe-market`):

```bash
cd /root/vibemom
docker compose up -d --build
docker compose exec -T bot pytest -q --tb=short
docker compose exec -T bot python scripts/audit_copy.py
```

**Optional (local without Docker):**

```bash
cd /root/vibemom
pip install -r requirements.txt
pip install -e .
python scripts/audit_copy.py
pytest -q --tb=short
```

**V2 feature flag:** Set `V2_ENABLED=true` in `.env` to use V2 schema (25+ steps, new answer keys) and Cabinet/Editor flow. Default `V2_ENABLED=false` keeps V1 questionnaire.

---

## 2. Expected outputs (success)

- **`docker compose up -d --build`**  
  - Exit code: **0**  
  - Logs: `Container ... Started` for `db` and `bot`.

- **`docker compose exec -T bot pytest -q --tb=short`**  
  - Exit code: **0**  
  - Line like: `..............` or `XX passed in N.NNs`.

- **`docker compose exec -T bot python scripts/audit_copy.py`**  
  - Exit code: **0**  
  - No stderr output.  
  - If exit code 1: COPY_ID missing in messages.py or Cyrillic outside messages.py (fix copy/COPY_IDS).

---

## 3. V2 feature flag (V2_ENABLED)

| File | Change | Why |
|------|--------|-----|
| **src/bot/config.py** | `v2_enabled: bool = False` (reads `V2_ENABLED` from `.env`) | Feature flag for V2 schema and Cabinet. |
| **src/bot/submission_engine.py** | `get_schema()` returns `get_project_submission_schema(Settings().v2_enabled)`; `get_current_step` and `validate_input` use `get_schema()`. | Engine uses V1 or V2 schema based on flag. |
| **src/bot/handlers/submit.py** | Use `get_schema()` for `first_step`, `get_step`; "edit" action uses schema to pick last step before preview (V1: contact_preferred, V2: goal_inbound_ready). | Router uses same schema as engine. |
| **.env.example** | `V2_ENABLED=false` | Document flag for deploy. |

**Unchanged (as required):**  
- DB schema, migrations, admin moderation logic, catalog/leads/request handlers — no edits.

---

## 4. If audit_copy.py fails

- **"COPY_ID referenced in code but missing in messages.py: X"**  
  - Add `X` to `messages.py` (constant + entry in `COPY_IDS`).

- **"Cyrillic outside messages.py: path:line"**  
  - Move user-facing Cyrillic into `messages.py` and use `get_copy("ID")`, or add that file to `CYRILLIC_EXCLUDE_FILES` in `scripts/audit_copy.py` if it’s not user-facing.

---

## 5. If pytest fails

- **Import errors**  
  - Run from repo root; use `docker compose exec -T bot pytest` (container has `PYTHONPATH=/app`) or local `pip install -e .`.

- **Schema/engine tests fail**  
  - Check that `src/bot/project_submission_schema.py` and `src/bot/submission_engine.py` exist and that all step `next_id`/`back_id`/`skip_id` reference valid state_ids.

- **Validator tests fail**  
  - Ensure `validate_url(text, max_len=None)`, `validate_url_or_empty`, `validate_max_len` exist in `src/bot/validators.py` with the signatures used in tests.
