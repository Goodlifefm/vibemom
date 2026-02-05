# Telegram Mini App "Кабинет" — архитектура (VibeMom)

Дата: 2026-02-05  
Цель: вынести "кабинетный" UX (проекты/каталог/реквесты/лиды) из чат-FSM в Telegram Mini App (WebApp), сохранив бота как входную точку и канал уведомлений.

---

## 0) Зачем это нужно

Текущие боли в чат-боте:
- UX ограничен Telegram UI: нельзя сделать полноценный "приложенческий" интерфейс.
- Кнопки/сценарии (Каталог/Реквест/Мои реквесты/Лиды) легко "ломаются" из-за конфликтов роутеров, reply vs inline, FSM, V1/V2 флагов.
- Трудно поддерживать "редактор" проекта в чате без визуального кабинета.

Решение:
- Mini App даёт полноценный UI: плитки, вкладки, карточки, фильтры, таблицы — "как приложение".
- Бот остаётся: меню/уведомления/быстрые действия + Deep Links в нужные экраны Mini App.

---

## 1) Что представляет собой Mini App

### 1.1 Основные разделы (MVP)
1) Dashboard
- Сводка: активный проект, статус, прогресс, последние действия
- Плитки: Мои проекты / Каталог / Реквесты / Мои реквесты / Лиды / Профиль
- Быстрые действия: "Создать проект", "Оставить заявку"

2) Проекты (My Projects)
- Список проектов пользователя
- Создать проект
- Карточка проекта:
  - статус (DRAFT / SUBMITTED / NEEDS_FIX / APPROVED / REJECTED / ARCHIVED)
  - прогресс (шаг X/Y)
  - ответы (редактируемые поля)
  - предпросмотр (как будет выглядеть пост)
  - "Отправить на модерацию" / "Внести правки"

3) Каталог (Marketplace)
- Список опубликованных/одобренных проектов
- Фильтры: ниша, стек, цена/диапазон, формат, статус
- Просмотр карточки проекта
- CTA: "Оставить реквест" / "Связаться"

4) Реквесты (Create Request)
- Форма создания заявки покупателя
- Поля: что ищу, бюджет, контакт
- Валидация и отправка

5) Мои реквесты (My Requests)
- Список заявок текущего пользователя
- Статус каждой заявки
- Matched-проекты (подобранные по критериям)
- Детали реквеста + обновления

6) Лиды (Leads) — только для роли seller/admin
- Список лидов + фильтры
- Карточка лида: контакт, источник, статус, заметки, следующий шаг
- (MVP) только просмотр + смена статуса + заметка

7) Профиль
- Имя/контакт/роль
- Настройки уведомлений (какие события бот присылает)

### 1.2 Расширения (после MVP)
- Загрузка файлов (скрины/демо/презентации) + CDN
- История изменений (audit log)
- Теги/хэштеги, рейтинг проектов
- Воронка лидов (pipeline)
- Платёжка/тарифы

---

## 2) Техническая архитектура

### 2.1 Компоненты
A) Telegram Bot (уже существует)
- Показывает меню и кнопку "Открыть кабинет"
- Шлёт уведомления: модерация/needs_fix/approve/reject/новые лиды
- Может запускать быстрый /resume и пушить в Mini App

B) Mini App Frontend (новый сервис)
- React + Vite (или Next.js)
- Telegram WebApp SDK
- UI-kit (Tailwind + shadcn/ui) — опционально

C) API Backend (новый сервис или модуль рядом с ботом)
- FastAPI (рекомендуется)
- Валидация Telegram initData
- REST API для projects/requests/leads/catalog
- Использует текущую PostgreSQL базу (или новую схему, но совместимую)

D) PostgreSQL (уже есть)
- Единый источник данных
- Таблицы users/submissions/admin_actions уже есть в боте; Mini App использует их или использует новые таблицы с маппингом.

---

## 3) Авторизация (Telegram initData)

Поток:
1) Пользователь открывает Mini App из бота (кнопка web_app).
2) WebApp получает initData от Telegram.
3) WebApp отправляет initData на API: POST /auth/telegram
4) API валидирует подпись (HMAC SHA-256 с bot_token) и извлекает user.id, username, first_name.
5) API создаёт/находит пользователя в БД и выдаёт access_token (JWT) + refresh (опционально).
6) Далее WebApp вызывает API с Bearer токеном.

Важные правила:
- Никаких логинов/паролей.
- initData валидируется сервером всегда.
- Роль (seller/admin) хранится в users.role или users.is_admin.

---

## 4) API контракты (MVP)

### Auth
- POST /auth/telegram
  - body: { initData: string }
  - returns: { access_token, user: { id, telegram_id, username, role } }

- GET /me

### Projects (используем submissions как "projects")
- GET /projects/my
- POST /projects
- GET /projects/{id}
- PUT /projects/{id}  (редактирование answers/current_step)
- POST /projects/{id}/preview
- POST /projects/{id}/submit  (SUBMITTED + revision++)
- POST /projects/{id}/archive

### Catalog
- GET /catalog/projects  (APPROVED/Published)
- GET /catalog/projects/{id}

### Requests
- POST /requests
- GET /requests/my
- GET /requests/{id}

### Leads (seller/admin)
- GET /leads
- PUT /leads/{id}  (status/note)

---

## 5) Согласование с текущим ботом (важно!)

### 5.1 Единая бизнес-логика
Принцип: "одна доменная логика — два клиента".
- Бот и WebApp вызывают одни и те же сервисы (renderer, validators, status transitions).
- Ключи answers JSON сохраняем стабильными (backward compatible).

### 5.2 Статусы и жизненный цикл
Использовать текущие статусы:
- DRAFT → SUBMITTED (pending) → NEEDS_FIX → повторная подача (revision++) → APPROVED или REJECTED → ARCHIVED

Revision strategy:
- обновлять ту же запись submission, увеличивать revision, обновлять submitted_at при каждом submit, логировать admin_actions.

### 5.3 Уведомления
API/бот должен отправлять уведомления в Telegram при событиях:
- NEEDS_FIX (с fix_request)
- APPROVED (с публикацией в FEED_CHAT_ID)
- REJECTED (с причиной)
- Новый лид / изменение лида (если нужна оперативность)

---

## 6) UI/UX принципы для "уникального дизайна"

- Главный экран — плитки (как на референс-скринах): 2 колонки, крупные тапы.
- Внутренние экраны — карточки со статусами и "бэйджами".
- Везде: понятные CTA ("Продолжить", "Предпросмотр", "Отправить").
- Обязательная согласованность предпросмотра и публикуемого поста:
  - один renderer для preview и feed
  - любые отличия — только в обёртке (например, добавление хэштегов)

---

## 7) План внедрения (по шагам)

M0 — Подготовка
- выбрать домен/хостинг фронта (Vercel/Netlify/Cloudflare Pages)
- выбрать API хостинг (VPS + Docker)
- добавить переменные окружения:
  - WEBAPP_URL
  - API_BASE_URL
  - BOT_TOKEN (на backend для проверки initData)

M1 — MVP auth + dashboard
- FastAPI /auth/telegram + /me
- простая WebApp страница "Dashboard" + проверка initData

M2 — Проекты (my projects)
- endpoints /projects/my, /projects/{id}
- UI списка + детали

M3 — Requests + Catalog
- requests endpoints + формы
- catalog read-only

M4 — Leads + роли
- роли, доступ, список лидов

M5 — Полировка и наблюдаемость
- /version в боте + build id на WebApp
- метрики (PostHog) опционально
- логирование API

---

## 8) Что считать "готово"
- Mini App открывается из бота и показывает dashboard.
- "Проекты": видны мои проекты, можно редактировать и отправлять на модерацию.
- "Реквесты": создаются и видны в "Мои реквесты".
- "Лиды": видны для роли seller/admin.
- Preview = Feed render (одинаковая структура).
- Бот присылает уведомления о модерации и публикует в канал при approve (если включено).
