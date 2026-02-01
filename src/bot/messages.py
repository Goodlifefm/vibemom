"""
All user-facing Russian copy. Single source: SPEC.md section 02_COPY.
Mirrored here; no Cyrillic user-facing strings elsewhere.
"""

START_MESSAGE = """
👋 Привет.

Ты в боте канала «Мам, я навайбкодил».
Здесь можно подать свой ноу-код проект или оставить заявку на подбор.

Команды: /catalog — каталог проектов, /submit — подать проект, /request — оставить заявку, /leads — мои лиды (продавцам), /my_requests — мои заявки (покупателям).
"""

SUBMIT_START = """
📤 Подача проекта

Ответь на несколько коротких вопросов — так твой проект увидят в каталоге.

Можно в любой момент вернуться назад или отменить: команда /start.
"""

SUBMIT_Q1_TITLE = """
📌 Название проекта

Одной строкой, как в витрине.

Примеры: «CRM для клининга в Notion», «Автозаявки в Telegram на Airtable».
"""

SUBMIT_Q2_DESCRIPTION = """
📝 Краткое описание

Что делает проект и для кого (1–3 предложения).

Пример: «База клиентов и договоров в Notion для маленькой компании. Руководитель видит все этапы сделки в одном месте».
"""

SUBMIT_Q3_STACK = """
⚙️ Стек и инструменты

Какие ноу-код инструменты используешь: Notion, Airtable, Make, Telegram-боты и т.п.

Пример: «Notion, Airtable, Make, Telegram».
"""

SUBMIT_Q4_LINK = """
🔗 Ссылка на проект или демо

Вставь рабочий URL: шаблон, демо-доступ, лендинг или канал.

Пример: https://notion.so/...
"""

SUBMIT_Q5_PRICE = """
💰 Цена

Напиши сумму (например: «5 000 ₽», «$50») или текст «по запросу» / «договорная».
"""

SUBMIT_Q6_CONTACT = """
📬 Как с тобой связаться

Telegram, email или другой контакт, по которому покупатель сможет написать.

Пример: @username или example@gmail.com
"""

SUBMIT_Q7_CONFIRM = """
✅ Всё верно?

Проверь данные выше. Отправь «Да» — проект уйдёт на модерацию. «Нет» — вернёшься к правкам.
"""

SUBMIT_SENT = """
Проект отправлен на модерацию. О результате узнаешь в боте.
"""

SUBMIT_CANCELLED = """
Подача отменена.
"""

REQUEST_START = """
Оставь заявку: что ищешь. Ответь на несколько вопросов.
"""

REQUEST_Q1_WHAT = """
Что ищешь? Опиши задачу или тип проекта.
"""

REQUEST_Q2_BUDGET = """
Бюджет (примерно или «не важно»).
"""

REQUEST_Q3_CONTACT = """
Как с тобой связаться (Telegram или другой контакт).
"""

REQUEST_Q4_CONFIRM = """
Всё верно? Отправь «да» чтобы отправить заявку, или «нет» чтобы править.
"""

REQUEST_SENT = """
Заявка отправлена. Подходящие проекты покажем в «Мои заявки» (/my_requests).
"""

REQUEST_CANCELLED = """
Заявка отменена.
"""

CATALOG_HEADER = """
📂 Каталог активных проектов.
"""

CATALOG_EMPTY = """
Пока нет активных проектов.
"""

CATALOG_ITEM_PREFIX = """
---
"""

LEADS_HEADER = """
📋 Твои лиды по проектам.
"""

LEADS_EMPTY = """
Пока нет лидов.
"""

MY_REQUESTS_HEADER = """
📋 Твои заявки и подобранные проекты.
"""

MY_REQUESTS_EMPTY = """
У тебя пока нет заявок. Создай заявку через /request.
"""

ADMIN_APPROVE = """
Проект одобрен и опубликован в каталоге.
"""

ADMIN_NEEDS_FIX = """
Проект отправлен на доработку. Автор увидит в боте.
"""

ADMIN_REJECT = """
Проект отклонён.
"""

ADMIN_MODERATE_PROMPT = """
Выбери действие: одобрить / на доработку / отклонить.
"""

ADMIN_NO_PENDING = """
Нет проектов на модерации.
"""

ERROR_NOT_TEXT = """
Нужен текст. Попробуй ещё раз.
"""

ERROR_INVALID_URL = """
Не похоже на ссылку. Введи корректный URL.
"""

ERROR_INVALID_YESNO = """
Ответь «да» или «нет».
"""

ERROR_MODERATION_SEND = """
Не удалось отправить в модерацию. Проверь ADMIN_CHAT_ID и права бота в группе.
"""

SAVE_DRAFT_OK = """
Черновик сохранён. Нажми «Продолжить», чтобы вернуться к заполнению.
"""

BTN_SUBMIT_TO_MODERATION = """
✅ Отправить на модерацию
"""

BTN_EDIT = """
✏️ Редактировать
"""

BTN_YES_SEND = """
✅ Да, отправить
"""

BTN_NO_RETURN = """
❌ Нет, вернуться
"""

BTN_RESUME = """
Продолжить
"""

SUBMIT_Q7_SEND_PROMPT = """
Отправить на модерацию? Нажми «Да» — проект уйдёт в чат модерации. «Нет» — вернёшься к правкам.
"""

# Navigation buttons (unified UX)
BACK_BUTTON = """
⬅️ Назад
"""

NEXT_BUTTON = """
➡️ Дальше
"""

SAVE_BUTTON = """
💾 Сохранить
"""

SKIP_BUTTON = """
⏭ Пропустить
"""

YES_BUTTON = """
Да
"""

NO_BUTTON = """
Нет
"""

BTN_APPROVE = """
✅ Одобрить
"""

BTN_NEEDS_FIX = """
🔄 На доработку
"""

BTN_REJECT = """
❌ Отклонить
"""

# Render template section labels (SPEC 05_RENDER_TEMPLATES)
TEMPLATE_EMOJI_TITLE = "🟢"
TEMPLATE_EMOJI_DESC = "📝"
TEMPLATE_SECTION_STACK = "⚙️ Стек"
TEMPLATE_SECTION_LINK = "🔗 Ссылка"
TEMPLATE_SECTION_PRICE = "💰 Цена"
TEMPLATE_SECTION_CONTACT = "📬 Контакт"
TEMPLATE_STACK = "Стек:"
TEMPLATE_LINK = "Ссылка:"
TEMPLATE_PRICE = "Цена:"
TEMPLATE_CONTACT_LABEL = "Контакт:"
TEMPLATE_CLAIM = "Заявка:"
TEMPLATE_BUDGET = "Бюджет:"

COPY_IDS = [
    "START_MESSAGE",
    "SUBMIT_START",
    "SUBMIT_Q1_TITLE",
    "SUBMIT_Q2_DESCRIPTION",
    "SUBMIT_Q3_STACK",
    "SUBMIT_Q4_LINK",
    "SUBMIT_Q5_PRICE",
    "SUBMIT_Q6_CONTACT",
    "SUBMIT_Q7_CONFIRM",
    "SUBMIT_SENT",
    "SUBMIT_CANCELLED",
    "REQUEST_START",
    "REQUEST_Q1_WHAT",
    "REQUEST_Q2_BUDGET",
    "REQUEST_Q3_CONTACT",
    "REQUEST_Q4_CONFIRM",
    "REQUEST_SENT",
    "REQUEST_CANCELLED",
    "CATALOG_HEADER",
    "CATALOG_EMPTY",
    "CATALOG_ITEM_PREFIX",
    "LEADS_HEADER",
    "LEADS_EMPTY",
    "MY_REQUESTS_HEADER",
    "MY_REQUESTS_EMPTY",
    "ADMIN_APPROVE",
    "ADMIN_NEEDS_FIX",
    "ADMIN_REJECT",
    "ADMIN_MODERATE_PROMPT",
    "ADMIN_NO_PENDING",
    "ERROR_NOT_TEXT",
    "ERROR_INVALID_URL",
    "ERROR_INVALID_YESNO",
    "ERROR_MODERATION_SEND",
    "SAVE_DRAFT_OK",
    "BTN_SUBMIT_TO_MODERATION",
    "BTN_EDIT",
    "BTN_YES_SEND",
    "BTN_NO_RETURN",
    "BTN_RESUME",
    "SUBMIT_Q7_SEND_PROMPT",
    "BACK_BUTTON",
    "NEXT_BUTTON",
    "SAVE_BUTTON",
    "SKIP_BUTTON",
    "YES_BUTTON",
    "NO_BUTTON",
    "BTN_APPROVE",
    "BTN_NEEDS_FIX",
    "BTN_REJECT",
    "TEMPLATE_EMOJI_TITLE",
    "TEMPLATE_EMOJI_DESC",
    "TEMPLATE_SECTION_STACK",
    "TEMPLATE_SECTION_LINK",
    "TEMPLATE_SECTION_PRICE",
    "TEMPLATE_SECTION_CONTACT",
    "TEMPLATE_STACK",
    "TEMPLATE_LINK",
    "TEMPLATE_PRICE",
    "TEMPLATE_CONTACT_LABEL",
    "TEMPLATE_CLAIM",
    "TEMPLATE_BUDGET",
]


def get_copy(copy_id: str) -> str:
    m = globals().get(copy_id)
    if m is None or not isinstance(m, str):
        return ""
    return m.strip()
