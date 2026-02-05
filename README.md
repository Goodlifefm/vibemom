# Мам, я навайбкодил — Telegram Marketplace Bot

MVP маркетплейса в Telegram: подача проектов продавцами, модерация админом, заявки покупателей, каталог, лиды и матчинг..

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

Запуск (сборка; миграции при AUTO_MIGRATE=true и APP_ENV!=production):

```bash
docker compose up --build
```

Или в фоне:

```bash
docker compose up -d --build
```

### Mini App API

Запуск только API сервиса:

```bash
docker compose up -d --build api
```

Проверка здоровья API:

```bash
curl http://localhost:8000/healthz
curl http://localhost:8000/version
```

Тестирование аутентификации (см. [docs/MINIAPP_API_SPEC.md](docs/MINIAPP_API_SPEC.md) для полного списка эндпоинтов):

```bash
# Получите initData из Telegram WebApp (window.Telegram.WebApp.initData)
# Пример запроса:
curl -X POST http://localhost:8000/auth/telegram \
  -H "Content-Type: application/json" \
  -d '{"initData": "query_id=...&user=...&auth_date=...&hash=..."}'

# После получения токена:
curl http://localhost:8000/me \
  -H "Authorization: Bearer <access_token>"

curl http://localhost:8000/projects/my \
  -H "Authorization: Bearer <access_token>"
```

#### Переменные окружения для API

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `API_JWT_SECRET` | Секрет для подписи JWT токенов | `change-me-in-production` |
| `API_JWT_TTL_MIN` | Время жизни токена в минутах | `43200` (30 дней) |
| `WEBAPP_ORIGINS` | Разрешённые CORS origins (через запятую) | — |

Бот поднимается после готовности БД. По умолчанию при старте выполняет миграции (`AUTO_MIGRATE=true`), но только если `APP_ENV!=production`.
Для продакшена установите `APP_ENV=production` (автомиграции всегда отключены) и запускайте миграции явно: `docker compose run --rm bot alembic upgrade head`.

### Smoke test (Docker)

Проверка, что стек поднимается и бот видит БД (без изменения поведения V1):

```bash
# 1. Собрать и запустить в фоне
docker compose up -d --build

# 2. Смотреть логи бота (ожидание: миграции при AUTO_MIGRATE=true и APP_ENV!=production, затем строка "Bot started, DB initialized")
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

## CI checks (local)

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
ruff check .
pytest
```

С аудитом копирайта (все тексты только в `messages.py`, все COPY_ID из кода есть в messages):

```bash
python scripts/audit_copy.py
```

## UX (V2): шаги и меню-кабинет

Все шаги формы выводятся по **единому шаблону**: «Шаг X из Y», затем заголовок шага (📌 и жирный текст), короткое пояснение, при необходимости блок «Что нужно сделать» и пример. Между блоками — пустые строки; везде используется `parse_mode="HTML"`. Кнопка **«☰ Меню»** (Reply-клавиатура) доступна всегда: при нажатии открывается **кабинет** с текущим проектом (или «Проект не задан»), текущим шагом X из Y и прогрессом в %. В кабинете: Продолжить, Текущий шаг (повтор текста шага), Проект (резюме данных), Начать заново (с подтверждением), Помощь. Навигация «Назад» / «Сохранить» по шагам не меняется.

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

Обязательные: `BOT_TOKEN`, `DATABASE_URL`. Остальные опциональны. Полный список в `.env.example`: `BOT_TOKEN`, `DATABASE_URL`, `ADMIN_CHAT_ID`, `FEED_CHAT_ID`, `ADMIN_IDS`, `LOG_LEVEL`, `APP_ENV`, `AUTO_MIGRATE`, `V2_ENABLED`, `V2_CANARY_MODE`, `V2_ALLOWLIST`. Поддерживается и `ADMIN_TELEGRAM_IDS` (если `ADMIN_IDS` не задан).

**Автопостинг в канал:** задайте в `.env` одну переменную `FEED_CHAT_ID` — канал для публикации после approve (V1 и V2). Значение: `@vibecode777` или числовой id канала (`-100...`). Если не задан — после approve пост в канал не отправляется (в лог пишется warning). Тест публикации: `python scripts/test_feed.py` (без `--dry-run` отправит тестовое сообщение); `python scripts/test_feed.py --dry-run` — только проверка конфига.

## Жизненный цикл статусов (V2)

DRAFT → SUBMITTED (pending) → NEEDS_FIX → повторная подача (revision++) → APPROVED или REJECTED. Отдельно может быть состояние ARCHIVED (архив).

## Стабильные ключи ответов (V2)

В `answers` (JSON) используются ключи: `title`, `subtitle`, `description`, `niche`, `what_done`, `status`, `stack_reason`, `time_spent`, `currency`, `cost`, `cost_max`, `potential`, `traction`, `gtm_stage`, `goal_pub`, `goal_inbound`, `channels`, `author_name`, `author_contact`, `links`.

## Canary-маршрутизация (V2)

- Если `V2_ENABLED=false` — все пользователи идут в V1.
- Если `V2_ENABLED=true` и `V2_CANARY_MODE=false` — все идут в V2.
- Если `V2_ENABLED=true` и `V2_CANARY_MODE=true` — V2 только для `ADMIN_IDS` или для tg_id из `V2_ALLOWLIST`; остальные остаются на V1.

## Mini App (Telegram WebApp)

Telegram Mini App — веб-интерфейс "Кабинет" для управления проектами.

### Быстрый старт

1. **Задеплоить frontend** на Vercel:
   ```bash
   cd services/webapp
   npm install
   vercel --prod
   ```

2. **Настроить BotFather**: 
   - `/mybots` → выбрать бота → Bot Settings → Menu Button → Configure
   - Указать URL Mini App: `https://your-app.vercel.app`

3. **Обновить .env на VPS**:
   ```env
   WEBAPP_URL=https://your-app.vercel.app
   API_PUBLIC_URL=https://api.yourdomain.com
   WEBAPP_ORIGINS=https://web.telegram.org
   ```

4. **Настроить Vercel Environment Variables**:
   - `VITE_API_PUBLIC_URL=https://api.yourdomain.com`

5. **Пересобрать контейнеры**:
   ```bash
   docker compose up -d --build bot api
   ```

### Mini App Quick Check

Быстрая проверка что всё работает:

```bash
# 1. На VPS: пересобрать и запустить
docker compose up -d --build api bot

# 2. Проверить health
curl http://localhost:8000/healthz
# Ожидается: {"status":"ok","database":"ok"}

# 3. Проверить version (должны быть WEBAPP_URL и API_PUBLIC_URL)
curl http://localhost:8000/version

# 4. Проверить env внутри контейнера
docker compose exec bot printenv | grep -E "(WEBAPP_URL|API_PUBLIC_URL)"
docker compose exec api printenv | grep -E "(WEBAPP_URL|API_PUBLIC_URL)"

# 5. Смотреть логи
docker compose logs -f bot api
```

В Telegram:
- `/version` — должен показать WEBAPP_URL и API_PUBLIC_URL
- Нажать кнопку **📱 Кабинет** — должен открыться Mini App со списком проектов

### Подробная документация

- [Mini App Deployment Guide](docs/MINIAPP_DEPLOY.md) — полное руководство по деплою

### Переменные окружения Mini App

| Переменная | Описание | Где |
|------------|----------|-----|
| `WEBAPP_URL` | HTTPS URL frontend (Vercel) | `.env` на VPS (bot + api) |
| `API_PUBLIC_URL` | Public API URL | `.env` на VPS + Vercel env как `VITE_API_PUBLIC_URL` |
| `WEBAPP_ORIGINS` | Доп. CORS origins | `.env` на VPS (api) |
| `TG_INIT_DATA_SKIP_VERIFY` | Пропуск проверки подписи (только dev!) | `.env` на VPS (api) |

## Deployment

Автодеплой на VPS при пуше в `main` или `master`: GitHub Actions по SSH заходит на сервер, обновляет код в `/root/vibemom`, пересобирает и перезапускает контейнеры (`docker compose up -d --build`).

### GitHub Secrets

В репозитории: **Settings → Secrets and variables → Actions** добавьте:

| Secret        | Описание |
|---------------|----------|
| `VPS_HOST`    | IP или hostname VPS (например `89.191.226.233`) |
| `VPS_USER`    | SSH-пользователь (например `root`) |
| `VPS_SSH_KEY` | Приватный SSH-ключ целиком (включая `-----BEGIN ... KEY-----` и `-----END ... KEY-----`) |
| `VPS_PORT`    | (опционально) Порт SSH, по умолчанию 22 |

### Генерация SSH-ключа (ed25519)

На своей машине:

```bash
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/vibemom_deploy -N ""
```

- Приватный ключ: `~/.ssh/vibemom_deploy` — содержимое целиком скопировать в секрет `VPS_SSH_KEY`.
- Публичный ключ: `~/.ssh/vibemom_deploy.pub` — добавить на VPS.

### Добавление публичного ключа на VPS

На VPS под пользователем, которым заходит Actions (например `root`):

```bash
mkdir -p ~/.ssh
chmod 700 ~/.ssh
echo "СОДЕРЖИМОЕ_ФАЙЛА_vibemom_deploy.pub" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

Или скопировать ключ вручную: `cat ~/.ssh/vibemom_deploy.pub` на локальной машине и вставить одну строку в `~/.ssh/authorized_keys` на VPS.

### Проверка

1. **Ручной запуск:** в GitHub: **Actions → Deploy to VPS → Run workflow** (кнопка Run workflow).
2. **По пушу:** сделайте push (или merge) в ветку `main` или `master` — workflow запустится автоматически.
3. В логах job должны быть: `git fetch`, `docker compose up -d --build`, `docker compose ps`, последние 120 строк логов сервиса `bot`.

Если основная ветка у вас не `main` и не `master`, в файле `.github/workflows/deploy.yml` измените строку `branches: [main, master]` на нужную ветку (например `branches: [production]`).

## 🎨 Design

- [Mini App Design System](docs/MINIAPP_DESIGN_SYSTEM.md) — дизайн-система, UI-паттерны, экраны и принципы

## 📐 Документация

- [Mini App Deployment Guide](docs/MINIAPP_DEPLOY.md) — руководство по деплою Mini App на Vercel + VPS
- [Mini App "Кабинет" — архитектура](docs/MINIAPP_CABINET_ARCHITECTURE.md) — план по выносу кабинетного UX в Telegram Mini App
- [Mini App API Specification](docs/MINIAPP_API_SPEC.md) — REST API для Mini App (auth, projects, endpoints, curl examples)
- [Mini App Data Contract](docs/MINIAPP_DATA_CONTRACT.md) — DTO-модели (с derived fields), V2 answers registry, legacy mapping, identity rules

## Спецификация

Единый источник правды: `SPEC.md` (секции 00–09: видение, роли, копирайт, FSM, шаблоны, схема БД, матчинг, права, не-цели).
