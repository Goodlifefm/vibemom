# V2 Editor-First — Summary of Changes

## What was added

- **Feature flag:** `V2_ENABLED` (env, default `false`). When `false`, `/start` and V1 flows unchanged. When `true`, `/start` opens V2 Cabinet.
- **Cabinet:** User dashboard with "Создать проект", "Мои проекты", "Как это работает". Resume button when `project_id` is in state. Create → new draft project → Dashboard. My projects → list (last 5) with "Открыть" per project.
- **Project Dashboard:** Per-project screen with title, status, revision. Buttons: Редактировать блоки, Предпросмотр, Отправить на модерацию, История, Архивировать, К проектам. Submit checks required fields via `missing_required_fields`; Preview/Submit reuse existing renderer and admin moderation flow. Archive sets status to `rejected` (no DB schema change).
- **Block Editor:** Block menu (blocks from `editor_schema`: Проект, Что сделано, Vibe-стек, Экономика, Цель, Автор, Дополнительно) with completion X/Y. "Заполнить по шагам" → guided flow (required fields in order). "Назад к проекту" → Dashboard.
- **Field registry:** `editor_schema.py` — BLOCKS, FIELDS (field_id, block_id, label, copy_id, answer_key, input_type, required, skippable, validator). Maps to project columns (title, description, stack, link, price, contact). Validators from existing validators module.
- **Universal field editor:** One flow: show question (copy_id), accept text, validate, save to project via `update_project_fields` (answers → project_fields), return to block menu. Back cancels; Skip (if skippable) saves empty and returns or continues in guided mode.
- **Guided flow:** "Заполнить по шагам" runs required fields in order; after each save opens next required field. "В редактор" exits to block menu.
- **Resume:** Cabinet shows "Продолжить редактирование" when state has `project_id`; opens Dashboard for that project.

## Files touched

| File | Change |
|------|--------|
| **src/bot/config.py** | Added `v2_enabled: bool = False`. |
| **src/bot/fsm/states.py** | Added `EditorStates.block_menu`, `EditorStates.field_edit`. |
| **src/bot/messages.py** | Added V2 copy (V2_CABINET_GREETING, V2_BTN_*, V2_DASHBOARD_*, V2_STATUS_*, V2_ARCHIVED, V2_SEND_MISSING_FIELDS, V2_SENT_TO_MODERATION, V2_EDITOR_*, V2_GUIDED_*, V2_BTN_RESUME_PROJECT) and COPY_IDS. |
| **src/bot/renderer.py** | Added `project_fields_to_answers(project)` for V2 (project row → answers dict). |
| **src/bot/services/project_service.py** | Added `list_projects_by_seller`, `get_project`, `update_project_fields`, `create_draft_project`. |
| **src/bot/editor_schema.py** | **NEW** — BLOCKS, FIELDS, get_block, get_field, get_fields_by_block, required_field_ids, missing_required_fields, VALIDATORS. |
| **src/bot/handlers/start.py** | If `v2_enabled`: call `show_cabinet(message, state)`; else unchanged. |
| **src/bot/handlers/__init__.py** | If `v2_enabled`: include cabinet, project_dashboard, editor routers. |
| **src/bot/handlers/cabinet.py** | **NEW** — Cabinet screen, Create, My projects, How it works, Open project, Resume. |
| **src/bot/handlers/project_dashboard.py** | **NEW** — Dashboard, Edit, Preview, Send, History, Archive, Back. Reuses renderer and admin moderation. |
| **src/bot/handlers/editor.py** | **NEW** — Block menu, guided flow, field edit (universal), Back/Skip, save to project. |
| **.env.example** | Added `V2_ENABLED=false`. |

## What was not changed

- DB schema and migrations.
- Admin moderation (admin.py), catalog, leads, request flows.
- V1 submit flow (submit.py) and FSM; it remains available when `V2_ENABLED=false` or as legacy path.
- Existing renderer (`render_project_post`, `answers_to_project_fields`) and validators.

## Autopublish to feed channel (V2.1)

После одобрения проекта модератором (approve) пост автоматически публикуется в канал, заданный в `FEED_CHAT_ID` (например `@vibecode777` или числовой id канала). Работает и для V1 (callback `mod_approve_{project_id}` в admin.py), и для V2 (callback `v2mod:approve:{submission_id}` в moderation.py).

- **Конфиг:** в `.env` одна переменная `FEED_CHAT_ID` — одно значение: `@vibecode777` или числовой id (`-100...`). Если не задан — публикация не выполняется, в лог пишется warning.
- **Формат поста:** заголовок, описание (~500 символов), контакт, цена, ссылка, хештеги по нише/стеку. Рендер: `src/v2/rendering/project_renderer.py` → `render_for_feed(answers)` или `render_for_feed(project_to_feed_answers(project))` для V1.
- **Логирование:** при успехе — `FEED publish ok project_id=... chat=... msg_id=...`; при ошибке — `logger.exception` и краткое уведомление админу в `ADMIN_CHAT_ID` (нет прав, чат не найден и т.п.).
- **Права:** бот должен быть админом канала с правом публикации сообщений.
- **Тест:** `python scripts/test_feed.py` — отправить тестовое сообщение в канал; `python scripts/test_feed.py --dry-run` — только проверить, что `FEED_CHAT_ID` задан.

## How to run V2

Set in `.env`:

```env
V2_ENABLED=true
FEED_CHAT_ID=@vibecode777
```

Restart bot. `/start` opens Cabinet; Create project → fill form (with step progress and hints) → Preview → Send to moderation. After admin approves, the project is auto-published to the feed channel. Admin flow unchanged.
