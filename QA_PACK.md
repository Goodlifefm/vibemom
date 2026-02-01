# QA Pack — VPS Commands & Expected Output

## 1. Exact terminal commands (max 5)

Run these **on the VPS** from the project root (e.g. `/root/vibemom` or `/root/vibe-market`):

```bash
cd /root/vibemom
docker compose up -d --build
docker compose exec -T bot python scripts/audit_copy.py
docker compose exec -T bot pytest tests/ -q --tb=short
docker compose exec -T bot pytest tests/test_project_submission_schema.py tests/test_submission_engine.py tests/test_renderer.py tests/test_validators.py -v --tb=short
```

**Optional (local without Docker):**

```bash
cd /root/vibemom
pip install -r requirements.txt
pip install -e .
python scripts/audit_copy.py
pytest tests/ -q --tb=short
```

---

## 2. Expected outputs (success)

- **`docker compose up -d --build`**  
  - Exit code: 0  
  - Logs: `Container ... Started` for `db` and `bot`.

- **`docker compose exec -T bot python scripts/audit_copy.py`**  
  - Exit code: **0**  
  - No stderr output.  
  - If exit code 1: COPY_ID missing in messages.py or Cyrillic outside messages.py (fix copy/COPY_IDS).

- **`docker compose exec -T bot pytest tests/ -q --tb=short`**  
  - Exit code: **0**  
  - Line like: `..............` or `XX passed in N.NNs`.

- **`docker compose exec -T bot pytest ... -v --tb=short`**  
  - Exit code: **0**  
  - Each test listed as `PASSED` (e.g. `test_schema_has_23_steps PASSED`, `test_validate_url_max_len PASSED`, `test_fsm_path_welcome_to_title_to_subtitle_back_to_title PASSED`).

---

## 3. Minimal code changes made (QA hardening)

| File | Change | Why |
|------|--------|-----|
| **tests/test_validators.py** | Import `validate_url_or_empty`, `validate_max_len`. Add `test_validate_url_max_len`, `test_validate_url_or_empty`, `test_validate_max_len`. | Cover new FSM validators (url max_len, url_or_empty, max_len edge cases). |
| **tests/test_submission_engine.py** | Add `test_fsm_path_welcome_to_title_to_subtitle_back_to_title`, `test_fsm_path_skip_from_title_subtitle_to_description_intro`, `test_fsm_path_preview_to_confirm_back_to_preview`. | Sanity-check Back/Skip/Next and resume-style paths. |
| **tests/test_renderer.py** | Add `test_render_project_post_section_order`. | Ensure section order (title → description → stack → link → price → contact) is stable. |
| **tests/test_project_submission_schema.py** | Add `test_every_step_copy_id_exists_in_messages`. | Ensures every schema step `copy_id` is in messages (aligns with audit_copy). |

**Unchanged (as required):**  
- DB schema, migrations, admin moderation logic, catalog/leads/request handlers — no edits.  
- FSM navigation (Back/Skip/Save/Resume) and renderer/validators logic — no refactor; only tests added/extended.

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
