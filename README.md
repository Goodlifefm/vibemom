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
# Заполните BOT_TOKEN и при необходимости ADMIN_TELEGRAM_IDS, DATABASE_URL
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

```bash
cp .env.example .env
# Заполните BOT_TOKEN в .env
docker-compose up --build
```

Бот поднимется после готовности БД и применит миграции при старте (`alembic upgrade head && python main.py`).

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
- `/admin` — модерация проектов (только для ADMIN_TELEGRAM_IDS)

## Спецификация

Единый источник правды: `SPEC.md` (секции 00–09: видение, роли, копирайт, FSM, шаблоны, схема БД, матчинг, права, не-цели).
