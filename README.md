# Мам, я навайбкодил — Telegram Marketplace Bot

MVP маркетплейса в Telegram: подача проектов продавцами, модерация админом, заявки покупателей, каталог, лиды и матчинг.

## Требования

- Python 3.12
- PostgreSQL
- Docker и docker-compose (для запуска в контейнерах)

## Локальная установка

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
```

Создайте `.env` из примера:

```bash
cp .env.example .env
# Заполните BOT_TOKEN и при необходимости ADMIN_IDS (или ADMIN_TELEGRAM_IDS), DATABASE_URL, V2_* при использовании V2
```

Миграции:

```bash
alembic upgrade head
```

Запуск бота:

```bash
python main.py
```

## Docker

Скопируйте `.env` и заполните `BOT_TOKEN` (и при необходимости `ADMIN_IDS`, `V2_ENABLED` и др.):

```bash
cp .env.example .env
```

Запуск (сборка и миграции при старте):

```bash
docker compose up --build
```

Или в фоне:

```bash
docker compose up -d --build
```

Бот поднимается после готовности БД и выполняет `alembic upgrade head && python main.py`.

### Smoke test (Docker)

Проверка, что стек поднимается и бот видит БД (без изменения поведения V1):

```bash
# 1. Собрать и запустить в фоне
docker compose up -d --build

# 2. Смотреть логи бота (ожидание: миграции, затем строка "Bot started, DB initialized")
docker compose logs -f bot

# 3. В другом терминале — проверка здоровья БД из контейнера бота (ожидание: вывод "OK", код 0)
docker compose exec bot python -m src.bot.health
```

**Ожидаемый вывод:**

- `docker compose up -d --build` — контейнеры `db` и `bot` созданы и запущены.
- `docker compose logs -f bot` — в логах есть строка вида `... | INFO | __main__ | Bot started, DB initialized`.
- `docker compose exec bot python -m src.bot.health` — в stdout одна строка `OK`, код возврата 0. При недоступной БД — сообщение в stderr и код 1.

## Тесты

Из корня репозитория (нужен `PYTHONPATH` или `pip install -e .` для импорта `src.bot`):

```bash
pytest
# или
python -m pytest tests/ -v
```

С аудитом копирайта (все тексты только в `messages.py`, все COPY_ID из кода есть в messages):

```bash
python scripts/audit_copy.py
```

## Команды бота

- `/start` — приветствие и список команд
- `/submit` — подать проект (7 шагов)
- `/request` — оставить заявку (покупатель)
- `/catalog` — каталог активных проектов
- `/leads` — лиды по своим проектам (продавец)
- `/my_requests` — мои заявки и подобранные проекты (покупатель)
- `/admin` — модерация проектов (только для ADMIN_IDS)
- `/stats` — статистика по V2-сабмишенам (только для ADMIN_IDS)

## Переменные окружения

Обязательные: `BOT_TOKEN`, `DATABASE_URL`. Остальные опциональны. Полный список в `.env.example`: `BOT_TOKEN`, `DATABASE_URL`, `ADMIN_CHAT_ID`, `ADMIN_IDS`, `LOG_LEVEL`, `V2_ENABLED`, `V2_CANARY_MODE`, `V2_ALLOWLIST`. Поддерживается и `ADMIN_TELEGRAM_IDS` (если `ADMIN_IDS` не задан).

## Жизненный цикл статусов (V2)

DRAFT → SUBMITTED (pending) → NEEDS_FIX → повторная подача (revision++) → APPROVED или REJECTED. Отдельно может быть состояние ARCHIVED (архив).

## Стабильные ключи ответов (V2)

В `answers` (JSON) используются ключи: `title`, `subtitle`, `description`, `niche`, `what_done`, `status`, `stack_reason`, `time_spent`, `currency`, `cost`, `cost_max`, `potential`, `traction`, `gtm_stage`, `goal_pub`, `goal_inbound`, `channels`, `author_name`, `author_contact`, `links`.

## Canary-маршрутизация (V2)

- Если `V2_ENABLED=false` — все пользователи идут в V1.
- Если `V2_ENABLED=true` и `V2_CANARY_MODE=false` — все идут в V2.
- Если `V2_ENABLED=true` и `V2_CANARY_MODE=true` — V2 только для `ADMIN_IDS` или для tg_id из `V2_ALLOWLIST`; остальные остаются на V1.

## Спецификация

Единый источник правды: `SPEC.md` (секции 00–09: видение, роли, копирайт, FSM, шаблоны, схема БД, матчинг, права, не-цели).
