# 00_PRODUCT_VISION

Telegram Marketplace bot «Мам, я навайбкодил» — MVP маркетплейса:
- Продавцы подают проекты (7 блоков).
- Админ модерирует: одобрить / на доработку / отклонить.
- Покупатели оставляют заявки.
- Каталог активных проектов (/catalog).
- Лиды: PROJECT_INTEREST и REQUEST_OFFER.
- Матчинг заявок покупателей к проектам по правилам.
- Мини-CRM: /leads для продавцов, /my_requests для покупателей.

---

# 01_ROLES

- **Seller** — подаёт проекты, получает лиды (/leads).
- **Buyer** — оставляет заявки, смотрит каталог, /my_requests.
- **Admin** — одобряет/отклоняет/на доработку проекты, админ-действия.

---

# 02_COPY

All user-facing Russian copy lives ONLY here.

[START_MESSAGE]
text = """
👋 Привет.
Ты в боте канала «Мам, я навайбкодил».
Здесь можно подать свой ноу-код проект или оставить заявку на подбор.
Команды: /catalog — каталог проектов, /submit — подать проект, /request — оставить заявку, /leads — мои лиды (продавцам), /my_requests — мои заявки (покупателям).
"""

[SUBMIT_START]
text = """
📤 Подача проекта

Ответь на несколько коротких вопросов — так твой проект увидят в каталоге.

Можно в любой момент вернуться назад или отменить: команда /start.
"""

[SUBMIT_Q1_TITLE]
text = """
📌 Название проекта

Одной строкой, как в витрине.

Примеры: «CRM для клининга в Notion», «Автозаявки в Telegram на Airtable».
"""

[SUBMIT_Q1_SUBTITLE]
text = """
📌 Подзаголовок (по желанию)

Короткая уточняющая строка под названием. Можно пропустить.
"""

[SUBMIT_Q2_DESCRIPTION]
text = """
📝 Краткое описание

Что делает проект и для кого (1–3 предложения).

Пример: «База клиентов и договоров в Notion для маленькой компании. Руководитель видит все этапы сделки в одном месте».
"""

[SUBMIT_Q2_INTRO]
text = """
📝 Вводное предложение (по желанию)

Одна фраза — суть проекта в одном предложении. Можно пропустить.
"""

[SUBMIT_Q2_WHAT_IT_DOES]
text = """
🧠 Что делает проект

Опиши главную задачу: какую проблему решает, что пользователь получает в итоге.

Коротко, по делу.
"""

[SUBMIT_Q2_FOR_WHOM]
text = """
👥 Для кого

Кто целевая аудитория: роль, ниша или тип бизнеса.

Пример: «Для владельцев малого бизнеса», «Для HR и рекрутеров».
"""

[SUBMIT_Q2_SUMMARY]
text = """
📋 Итог описания (по желанию)

Одно предложение — резюме для каталога. Можно пропустить.
"""

[SUBMIT_Q2_KEY_FEATURES]
text = """
✨ Ключевые фичи (по желанию)

2–3 главные возможности. Можно пропустить — нажми «Пропустить».
"""

[SUBMIT_Q2_SKIP]
text = """
Пропустить
"""

[SUBMIT_Q3_STACK]
text = """
⚙️ Стек и инструменты

Какие ноу-код инструменты используешь: Notion, Airtable, Make, Telegram-боты и т.п.

Пример: «Notion, Airtable, Make, Telegram».
"""

[SUBMIT_Q3_STACK_LIST]
text = """
⚙️ Список инструментов (по желанию)

Перечисли через запятую или с новой строки. Можно пропустить.
"""

[SUBMIT_Q3_OTHER_TOOLS]
text = """
🔧 Доп. инструменты (по желанию)

Ещё интеграции, шаблоны, скрипты. Можно пропустить.
"""

[SUBMIT_Q3_CONFIRM]
text = """
⚙️ Стек полный?

Дополнить список инструментов? Можно пропустить.
"""

[SUBMIT_Q4_LINK]
text = """
🔗 Ссылка на проект или демо

Вставь рабочий URL: шаблон, демо-доступ, лендинг или канал.

Пример: https://notion.so/...
"""

[SUBMIT_Q5_PRICE]
text = """
💰 Цена

Напиши сумму (например: «5 000 ₽», «$50») или текст «по запросу» / «договорная».
"""

[SUBMIT_Q6_CONTACT]
text = """
📬 Как с тобой связаться

Telegram, email или другой контакт, по которому покупатель сможет написать.

Пример: @username или example@gmail.com
"""

[SUBMIT_Q4_LINK_DEMO]
text = """
🔗 Доп. ссылка (по желанию)

Вторая ссылка: демо, инструкция, видео. Можно пропустить.
"""

[SUBMIT_Q4_LINK_CONFIRM]
text = """
🔗 Ещё ссылка? (по желанию)

Можно добавить ссылку на отзывы или кейс. Пропустить — к цене.
"""

[SUBMIT_Q5_PRICE_NOTE]
text = """
💰 Уточнение по оплате (по желанию)

Условия оплаты, рассрочка, пакеты. Можно пропустить.
"""

[SUBMIT_Q5_CURRENCY]
text = """
💰 Валюта (по желанию)

₽ / $ / € или «любая». Можно пропустить.
"""

[SUBMIT_Q6_CONTACT_EXTRA]
text = """
📬 Доп. контакт (по желанию)

Ещё способ связи. Можно пропустить.
"""

[SUBMIT_Q6_PREFERRED]
text = """
📬 Предпочтительный способ (по желанию)

«Лучше в Telegram» / «Пишите на email». Можно пропустить.
"""

[SUBMIT_PREVIEW]
text = """
👀 Предпросмотр карточки

Ниже — как твой проект будет выглядеть в каталоге. Проверь и нажми «Далее», чтобы перейти к подтверждению.
"""

[NEXT_BUTTON]
text = """
Далее →
"""

[SUBMIT_Q7_CONFIRM]
text = """
✅ Всё верно?

Проверь данные выше. Отправь «Да» — проект уйдёт на модерацию. «Нет» — вернёшься к правкам.
"""

[SUBMIT_SENT]
text = """
Проект отправлен на модерацию. О результате узнаешь в боте.
"""

[SUBMIT_CANCELLED]
text = """
Подача отменена.
"""

[REQUEST_START]
text = """
Оставь заявку: что ищешь. Ответь на несколько вопросов.
"""

[REQUEST_Q1_WHAT]
text = """
Что ищешь? Опиши задачу или тип проекта.
"""

[REQUEST_Q2_BUDGET]
text = """
Бюджет (примерно или «не важно»).
"""

[REQUEST_Q3_CONTACT]
text = """
Как с тобой связаться (Telegram или другой контакт).
"""

[REQUEST_Q4_CONFIRM]
text = """
Всё верно? Отправь «да» чтобы отправить заявку, или «нет» чтобы править.
"""

[REQUEST_SENT]
text = """
Заявка отправлена. Подходящие проекты покажем в «Мои заявки» (/my_requests).
"""

[REQUEST_CANCELLED]
text = """
Заявка отменена.
"""

[CATALOG_HEADER]
text = """
📂 Каталог активных проектов.
"""

[CATALOG_EMPTY]
text = """
Пока нет активных проектов.
"""

[CATALOG_ITEM_PREFIX]
text = """
---
"""

[LEADS_HEADER]
text = """
📋 Твои лиды по проектам.
"""

[LEADS_EMPTY]
text = """
Пока нет лидов.
"""

[MY_REQUESTS_HEADER]
text = """
📋 Твои заявки и подобранные проекты.
"""

[MY_REQUESTS_EMPTY]
text = """
У тебя пока нет заявок. Создай заявку через /request.
"""

[ADMIN_APPROVE]
text = """
Проект одобрен и опубликован в каталоге.
"""

[ADMIN_NEEDS_FIX]
text = """
Проект отправлен на доработку. Автор увидит в боте.
"""

[ADMIN_REJECT]
text = """
Проект отклонён.
"""

[ADMIN_MODERATE_PROMPT]
text = """
Выбери действие: одобрить / на доработку / отклонить.
"""

[ADMIN_NO_PENDING]
text = """
Нет проектов на модерации.
"""

[ERROR_NOT_TEXT]
text = """
Нужен текст. Попробуй ещё раз.
"""

[ERROR_INVALID_URL]
text = """
Не похоже на ссылку. Введи корректный URL.
"""

[ERROR_INVALID_YESNO]
text = """
Ответь «да» или «нет».
"""

[BACK_BUTTON]
text = """
← Назад
"""

[YES_BUTTON]
text = """
Да
"""

[NO_BUTTON]
text = """
Нет
"""

[BTN_APPROVE]
text = """
✅ Одобрить
"""

[BTN_NEEDS_FIX]
text = """
🔄 На доработку
"""

[BTN_REJECT]
text = """
❌ Отклонить
"""

---

# 03_FSM_PROJECT_SUBMISSION

Seller project submission: expanded from 7 blocks into a detailed step-by-step FSM. Each logical question = its own state. 23 states total. Logical grouping preserved (title → description → stack → link → price → contact → preview → confirm).

| state_id | copy_id | input_type | validation | next_state | skip_state | back_state |
|----------|---------|------------|------------|------------|------------|------------|
| ProjectSubmission.welcome | SUBMIT_START | buttons | — | ProjectSubmission.title | — | — |
| ProjectSubmission.title | SUBMIT_Q1_TITLE | text | non_empty, max 200 | ProjectSubmission.title_subtitle | — | ProjectSubmission.welcome |
| ProjectSubmission.title_subtitle | SUBMIT_Q1_SUBTITLE | text | max 150 | ProjectSubmission.description_intro | ProjectSubmission.description_intro | ProjectSubmission.title |
| ProjectSubmission.description_intro | SUBMIT_Q2_INTRO | text | max 300 | ProjectSubmission.description_what | ProjectSubmission.description_what | ProjectSubmission.title_subtitle |
| ProjectSubmission.description_what | SUBMIT_Q2_WHAT_IT_DOES | text | non_empty, max 1000 | ProjectSubmission.description_audience | — | ProjectSubmission.description_intro |
| ProjectSubmission.description_audience | SUBMIT_Q2_FOR_WHOM | text | non_empty, max 500 | ProjectSubmission.description_summary | — | ProjectSubmission.description_what |
| ProjectSubmission.description_summary | SUBMIT_Q2_SUMMARY | text | max 400 | ProjectSubmission.description_features | ProjectSubmission.description_features | ProjectSubmission.description_audience |
| ProjectSubmission.description_features | SUBMIT_Q2_KEY_FEATURES | multi | max 500 | ProjectSubmission.stack | ProjectSubmission.stack | ProjectSubmission.description_summary |
| ProjectSubmission.stack | SUBMIT_Q3_STACK | text | non_empty, max 500 | ProjectSubmission.stack_list | — | ProjectSubmission.description_features |
| ProjectSubmission.stack_list | SUBMIT_Q3_STACK_LIST | text | max 400 | ProjectSubmission.stack_other | ProjectSubmission.stack_other | ProjectSubmission.stack |
| ProjectSubmission.stack_other | SUBMIT_Q3_OTHER_TOOLS | text | max 300 | ProjectSubmission.stack_confirm | ProjectSubmission.link | ProjectSubmission.stack_list |
| ProjectSubmission.stack_confirm | SUBMIT_Q3_CONFIRM | buttons | — | ProjectSubmission.link | ProjectSubmission.link | ProjectSubmission.stack_other |
| ProjectSubmission.link | SUBMIT_Q4_LINK | text | url, max 1000 | ProjectSubmission.link_demo | — | ProjectSubmission.stack_confirm |
| ProjectSubmission.link_demo | SUBMIT_Q4_LINK_DEMO | text | url_or_empty, max 1000 | ProjectSubmission.link_confirm | ProjectSubmission.link_confirm | ProjectSubmission.link |
| ProjectSubmission.link_confirm | SUBMIT_Q4_LINK_CONFIRM | text | url_or_empty, max 1000 | ProjectSubmission.price | ProjectSubmission.price | ProjectSubmission.link_demo |
| ProjectSubmission.price | SUBMIT_Q5_PRICE | text | non_empty, max 200 | ProjectSubmission.price_note | — | ProjectSubmission.link_confirm |
| ProjectSubmission.price_note | SUBMIT_Q5_PRICE_NOTE | text | max 300 | ProjectSubmission.price_currency | ProjectSubmission.price_currency | ProjectSubmission.price |
| ProjectSubmission.price_currency | SUBMIT_Q5_CURRENCY | text | max 50 | ProjectSubmission.contact | ProjectSubmission.contact | ProjectSubmission.price_note |
| ProjectSubmission.contact | SUBMIT_Q6_CONTACT | text | non_empty, max 200 | ProjectSubmission.contact_extra | — | ProjectSubmission.price_currency |
| ProjectSubmission.contact_extra | SUBMIT_Q6_CONTACT_EXTRA | text | max 200 | ProjectSubmission.contact_preferred | ProjectSubmission.contact_preferred | ProjectSubmission.contact |
| ProjectSubmission.contact_preferred | SUBMIT_Q6_PREFERRED | text | max 100 | ProjectSubmission.preview | ProjectSubmission.preview | ProjectSubmission.contact_extra |
| ProjectSubmission.preview | SUBMIT_PREVIEW | buttons | — | ProjectSubmission.confirm | — | ProjectSubmission.contact_preferred |
| ProjectSubmission.confirm | SUBMIT_Q7_CONFIRM | buttons | yes_no | (submit) / (cancel) | — | ProjectSubmission.preview |

Notes:
- **description_summary**, **description_features**, **stack_list**, **stack_other**, **stack_confirm**, **link_demo**, **link_confirm**, **price_note**, **price_currency**, **contact_extra**, **contact_preferred**: OPTIONAL skip where indicated; skip_state = next step in flow.
- **description_features**: input_type `multi` = text or button [SUBMIT_Q2_SKIP].
- **preview**: shows rendered PROJECT_POST; button [NEXT_BUTTON] → confirm.
- **back_state**: where «Назад» leads. welcome has no back.
- All copy_id above exist in 02_COPY. Total: 23 states.

---

# 04_FSM_BUYER_REQUEST

Buyer request flow.

| state_id | copy_id | input_type | validation | next_state | skip_state | back_state |
|----------|---------|------------|------------|------------|------------|------------|
| BuyerRequest.what | REQUEST_Q1_WHAT | text | non_empty, max 2000 | BuyerRequest.budget | — | — |
| BuyerRequest.budget | REQUEST_Q2_BUDGET | text | non_empty, max 200 | BuyerRequest.contact | — | BuyerRequest.what |
| BuyerRequest.contact | REQUEST_Q3_CONTACT | text | non_empty, max 200 | BuyerRequest.confirm | — | BuyerRequest.budget |
| BuyerRequest.confirm | REQUEST_Q4_CONFIRM | buttons | yes_no | (submit) / (cancel) | — | BuyerRequest.contact |

---

# 05_RENDER_TEMPLATES

[PROJECT_POST]
Template ID: PROJECT_POST
Placeholders: {title}, {description}, {stack}, {link}, {price}, {contact}
Purpose: Marketplace vitrina — preview before submission and catalog card. Clear sections, visual spacing, emojis for scanability by business users.

Format:
```
🟢 {title}

📝 {description}

⚙️ Стек
{stack}

🔗 Ссылка
{link}

💰 Цена
{price}

📬 Контакт
{contact}
```

**POST_PLACEHOLDERS_MAPPING**

How rendered post placeholders are composed from FSM answers (state_id = answer key). Skipped/optional steps contribute empty string or are omitted.

| placeholder | FSM answer keys (in order) |
|-------------|---------------------------|
| {title} | ProjectSubmission.title, ProjectSubmission.title_subtitle (optional) |
| {description} | ProjectSubmission.description_intro (optional), ProjectSubmission.description_what, ProjectSubmission.description_audience, ProjectSubmission.description_summary (optional), ProjectSubmission.description_features (optional) |
| {stack} | ProjectSubmission.stack, ProjectSubmission.stack_list (optional), ProjectSubmission.stack_other (optional) |
| {link} | ProjectSubmission.link, ProjectSubmission.link_demo (optional), ProjectSubmission.link_confirm (optional) |
| {price} | ProjectSubmission.price, ProjectSubmission.price_note (optional), ProjectSubmission.price_currency (optional) |
| {contact} | ProjectSubmission.contact, ProjectSubmission.contact_extra (optional), ProjectSubmission.contact_preferred (optional) |

Combine multiple values with newline or separator as needed for display. Single-field DB storage (06) uses the same logical field; implementation concatenates or picks primary per field.

---

[BUYER_REQUEST_SUMMARY]
Template ID: BUYER_REQUEST_SUMMARY
Placeholders: {what}, {budget}, {contact}
Format:
---
Заявка: {what}
Бюджет: {budget}
Контакт: {contact}
---

---

# 06_DATABASE_SCHEMA

**Enums:**
- ProjectStatus: draft, pending, needs_fix, approved, rejected
- LeadType: PROJECT_INTEREST, REQUEST_OFFER

**Tables:**

- **user**
  - id (PK, bigint)
  - telegram_id (bigint, unique)
  - username (varchar, nullable)
  - full_name (varchar, nullable)
  - is_admin (boolean, default false)
  - created_at, updated_at (timestamptz)

- **project**
  - id (PK, uuid)
  - seller_id (FK -> user.id)
  - title, description, stack, link, price, contact (varchar/text)
  - status (enum ProjectStatus, default pending)
  - moderation_comment (text, nullable)
  - created_at, updated_at (timestamptz)

- **buyer_request**
  - id (PK, uuid)
  - buyer_id (FK -> user.id)
  - what (text)
  - budget (varchar)
  - contact (varchar)
  - created_at, updated_at (timestamptz)

- **lead**
  - id (PK, uuid)
  - project_id (FK -> project.id)
  - buyer_request_id (FK -> buyer_request.id, nullable)
  - lead_type (enum LeadType)
  - created_at (timestamptz)

**Relations:**
- project.seller_id -> user.id
- buyer_request.buyer_id -> user.id
- lead.project_id -> project.id
- lead.buyer_request_id -> buyer_request.id (nullable for PROJECT_INTEREST from catalog)

---

# 07_MATCHING_RULES

- **Scoring** (buyer_request -> projects):
  - Keyword overlap (what vs project title+description): +10 per matching word (stemmed/stopwords excluded), max +50.
  - Budget mention: if request budget ~ project price range: +20.
  - Default (no match): 0.
- **Threshold:** score >= 10 to show project in «Мои заявки» for that request.
- **Fallback:** If no project scores >= 10, show empty list for that request (no random suggestions).

---

# 08_SECURITY_AND_PERMISSIONS

- **Admin-only:** Moderation (approve / needs_fix / reject). Access to list pending projects and moderate.
- **Access checks:** /leads — only projects owned by current user (seller). /my_requests — only buyer_requests of current user. Catalog — only projects with status = approved.

---

# 09_NON_GOALS

- Payments and escrow.
- Notifications (push/email) — only in-bot.
- Multi-language.
- Editing project after approval (only new submission).
- Rate limiting / anti-spam (future).
- Webhook mode (only long polling in MVP).
