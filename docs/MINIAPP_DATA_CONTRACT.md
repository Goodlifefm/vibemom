# Mini App — Data Contract

Версия: 1.0  
Дата: 2026-02-05  
Статус: Canonical  
Источник истины: `submission.answers JSONB` + `ProjectStatus enum`

---

## A) Глоссарий сущностей

### User

Пользователь системы (продавец, покупатель или админ).

| Поле | Тип | Nullable | Описание |
| ------ | ----- | ---------- | ---------- |
| `id` | BigInteger | ✗ | Internal PK (auto-increment) |
| `telegram_id` | BigInteger | ✗ | Telegram user ID (unique) |
| `username` | String(255) | ✓ | Telegram @username |
| `full_name` | String(255) | ✓ | Имя из Telegram (first_name + last_name) |
| `is_admin` | Boolean | ✗ | Роль админа (default: false) |
| `created_at` | DateTime | ✗ | Дата регистрации |
| `updated_at` | DateTime | ✗ | Последнее обновление |

**Роли:**

- `seller` — владеет проектами, видит свои лиды
- `buyer` — создаёт реквесты, смотрит каталог
- `admin` — модерация, is_admin=true

---

### Submission / ProjectDraft

V2 submission — черновик/проект на всех этапах жизненного цикла.

| Поле | Тип | Nullable | Описание |
| ------ | ----- | ---------- | ---------- |
| `id` | UUID | ✗ | Primary key |
| `user_id` | BigInteger | ✗ | FK → User.id (владелец) |
| `project_id` | UUID | ✓ | FK → Project.id (V1 legacy link) |
| `status` | ProjectStatus | ✗ | Статус (draft/pending/needs_fix/approved/rejected) |
| `revision` | Integer | ✗ | Номер редакции (++ при каждом submit) |
| `answers` | JSONB | ✓ | Ответы пользователя (см. секцию C) |
| `rendered_post` | Text | ✓ | Сохранённый HTML поста (при submit) |
| `current_step` | String(50) | ✓ | Текущий шаг визарда (q1..q19) |
| `fix_request` | Text | ✓ | Комментарий модератора (при NEEDS_FIX) |
| `moderated_at` | DateTime | ✓ | Когда промодерировали |
| `submitted_at` | DateTime | ✓ | Когда отправили на модерацию |
| `created_at` | DateTime | ✗ | Дата создания |
| `updated_at` | DateTime | ✗ | Последнее обновление |

---

### PublicProject

Опубликованный проект в каталоге (APPROVED submissions).

**Источник:** `Submission WHERE status = 'approved'`

Отображаемые поля формируются из `answers` + metadata:

- title, subtitle, niche, description
- what_done, status, stack_reason
- price (из budget_* или cost/cost_max/currency)
- contact (author_name + author_contact)
- links

---

### Request (BuyerRequest)

Заявка покупателя.

| Поле | Тип | Nullable | Описание |
| ------ | ----- | ---------- | ---------- |
| `id` | UUID | ✗ | Primary key |
| `buyer_id` | BigInteger | ✗ | FK → User.id |
| `what` | Text | ✗ | Что ищет покупатель |
| `budget` | String(200) | ✗ | Бюджет (свободный формат) |
| `contact` | String(200) | ✗ | Контакт покупателя |
| `created_at` | DateTime | ✗ | Дата создания |
| `updated_at` | DateTime | ✗ | Последнее обновление |

---

### Lead

Лид — связь между проектом и интересом покупателя.

| Поле | Тип | Nullable | Описание |
| ------ | ----- | ---------- | ---------- |
| `id` | UUID | ✗ | Primary key |
| `project_id` | UUID | ✗ | FK → Project.id |
| `buyer_request_id` | UUID | ✓ | FK → BuyerRequest.id (если из реквеста) |
| `lead_type` | LeadType | ✗ | PROJECT_INTEREST / REQUEST_OFFER |
| `created_at` | DateTime | ✗ | Дата создания |

**LeadType:**

- `PROJECT_INTEREST` — прямой интерес к проекту
- `REQUEST_OFFER` — предложение по реквесту

---

## B) Единая DTO-модель для фронта

### 1) ProjectListItemDTO

Элемент списка "Мои проекты".

```typescript
interface ProjectListItemDTO {
  // Required — всегда присутствуют
  id: string;                    // UUID
  status: ProjectStatus;         // "draft" | "pending" | "needs_fix" | "approved" | "rejected"
  revision: number;              // >= 0
  created_at: string;            // ISO8601
  updated_at: string;            // ISO8601
  
  // Derived — вычисляемые на backend
  title_short: string;           // answers.title truncated to 50 chars + "..."
  completion_percent: number;    // 0-100, (filled_steps / total_steps) * 100
  next_action: NextAction;       // см. ниже
  
  // Optional — могут отсутствовать
  current_step: string | null;   // "q1".."q19" | "preview" | null
  submitted_at: string | null;   // ISO8601 | null
  has_fix_request: boolean;      // fix_request != null
}

type ProjectStatus = "draft" | "pending" | "needs_fix" | "approved" | "rejected";

interface NextAction {
  action: "continue" | "fix" | "wait" | "view" | "archived";
  label: string;    // UI label, e.g. "Продолжить заполнение"
  cta_enabled: boolean;
}
```

**Правила `next_action`:**

| status | next_action.action | label |
| -------- | ------------------- | ------- |
| draft | continue | "Продолжить заполнение" |
| needs_fix | fix | "Внести правки" |
| pending | wait | "Ожидает модерации" |
| approved | view | "Посмотреть публикацию" |
| rejected | archived | "Отклонён" |

**Правила `completion_percent`:**

```text
filled_steps = count of non-empty answer_keys
total_steps = 19 (q1..q19)
completion_percent = round(filled_steps / total_steps * 100)
```

---

### 2) ProjectDetailsDTO

Полная карточка проекта (для редактирования/просмотра).

```typescript
interface ProjectDetailsDTO {
  // Core
  id: string;
  status: ProjectStatus;
  revision: number;
  current_step: string | null;
  
  // Answers — полный snapshot
  answers: ProjectAnswers;       // см. секцию C
  
  // Moderation
  fix_request: string | null;    // комментарий модератора
  moderated_at: string | null;   // ISO8601
  
  // Rendered
  rendered_post: string | null;  // HTML (сохранённый при submit)
  
  // Timestamps
  created_at: string;
  updated_at: string;
  submitted_at: string | null;
  
  // Derived
  title_short: string;
  completion_percent: number;
  next_action: NextAction;
  missing_required_fields: string[];  // field_ids, которые пусты
  is_submittable: boolean;            // missing_required_fields.length === 0 && status in [draft, needs_fix]
}
```

---

### 3) ProjectEditorDTO

Схема полей для формы редактора.

```typescript
interface ProjectEditorDTO {
  blocks: EditorBlock[];
  fields: EditorField[];
  steps: StepConfig[];           // Wizard steps q1..q19
  current_step: string | null;   // Где остановился пользователь
  answers: ProjectAnswers;       // Текущие значения
}

interface EditorBlock {
  block_id: string;              // "author" | "project" | "done" | "stack" | "econ" | "gtm" | "goal" | "links"
  label: string;                 // "Автор", "Проект", ...
  emoji: string;                 // "👤", "📌", ...
  fields: string[];              // field_ids в этом блоке
  completion: number;            // 0-100%, заполненность блока
}

interface EditorField {
  field_id: string;              // Уникальный ID поля
  block_id: string;              // В каком блоке
  label: string;                 // UI label
  answer_key: string;            // Ключ в answers JSON
  input_type: InputType;         // "text" | "textarea" | "select" | "multi_choice" | "links" | "budget"
  required: boolean;
  skippable: boolean;            // Можно пропустить (optional step)
  validator: string;             // "non_empty" | "contact" | "link" | "budget" | "time"
  choices?: string[];            // Для select/multi_choice
  placeholder?: string;
  help_text?: string;
}

interface StepConfig {
  step_key: string;              // "q1".."q19", "preview"
  answer_key: string;            // Какой ключ заполняется
  copy_id: string;               // ID текста промпта
  optional: boolean;
  multi_link: boolean;           // q19 — коллектор ссылок
  next_step: string | null;
  prev_step: string | null;
}

type InputType = "text" | "textarea" | "select" | "multi_choice" | "links" | "budget";
```

---

### 4) PublicProjectCardDTO

Карточка проекта в каталоге.

```typescript
interface PublicProjectCardDTO {
  // Identity
  id: string;
  
  // Display fields (derived from answers)
  title: string;                 // answers.title + answers.subtitle
  description_short: string;     // answers.description (truncated 200 chars)
  niche: string;                 // answers.niche
  
  // Price (computed)
  price_display: string;         // "скрыта" | "50 000 ₽" | "50 000–100 000 $"
  price_min: number | null;      // For filtering
  price_max: number | null;
  currency: string;              // "RUB" | "USD" | "EUR"
  
  // Author
  author_name: string;           // answers.author_name
  
  // Links
  primary_link: string | null;   // First from answers.links[]
  
  // Meta
  created_at: string;
  
  // Computed for UI
  tags: string[];                // Generated from niche + stack
}
```

---

### 5) RequestDTO

Заявка покупателя.

```typescript
interface RequestDTO {
  id: string;
  what: string;                  // Что ищет
  budget: string;                // Бюджет (text)
  contact: string;               // Контакт
  created_at: string;
  updated_at: string;
  
  // Derived
  matched_projects_count: number;  // Сколько проектов подошло
}

interface RequestDetailsDTO extends RequestDTO {
  matched_projects: PublicProjectCardDTO[];
}

interface RequestCreateDTO {
  what: string;                  // required, max 1000 chars
  budget: string;                // required, max 200 chars
  contact: string;               // required, max 200 chars
}
```

---

### 6) LeadDTO

Лид для продавца.

```typescript
interface LeadDTO {
  id: string;
  project_id: string;
  project_title: string;         // Derived from project.answers.title
  lead_type: "PROJECT_INTEREST" | "REQUEST_OFFER";
  
  // Buyer info
  contact_info: {
    telegram_id: number;
    username: string | null;
    full_name: string | null;
  };
  
  // If from request
  buyer_request_id: string | null;
  buyer_request_preview: string | null;  // First 100 chars of what
  
  created_at: string;
}

interface LeadListDTO {
  items: LeadDTO[];
  total: number;
  limit: number;
  offset: number;
}
```

---

## C) answers JSON keys — единый справочник

### Таблица ключей

| json_key | Meaning | UI Label | Source Step | Example Value | Validation |
| ---------- | --------- | ---------- | ------------- | --------------- | ------------ |
| `title` | Название проекта | Название | q1 | "SaaS для HR" | non_empty, max 200 |
| `description` | Описание проекта | Описание | q2 | "Автоматизация рекрутинга..." | non_empty, max 1000 |
| `contact` | Основной контакт | Контакт | q3 | "@username" | contact validator |
| `subtitle` | Подзаголовок/слоган | Подзаголовок | q4 | "MVP готов, ищу покупателя" | non_empty, max 200 |
| `niche` | Ниша/индустрия | Ниша | q5 | "B2B SaaS, HR-tech" | non_empty, max 200 |
| `what_done` | Что уже сделано | Что сделано | q6 | "MVP, 10 платящих клиентов" | non_empty, max 500 |
| `status` | Статус продукта | Статус продукта | q7 | "working" / "mvp" / "idea" | non_empty |
| `stack_reason` | Стек и почему выбран | Стек (опц.) | q8 | "Python/FastAPI — быстрая разработка" | optional, max 500 |
| `time_spent` | Время на разработку | Время | q9 | "6 месяцев" | time validator |
| `budget_min` | Мин. цена | Цена от | q10 | 50000 | number, >= 0 |
| `budget_max` | Макс. цена | Цена до | q10 | 100000 | number, >= budget_min |
| `budget_currency` | Валюта | Валюта | q10 | "RUB" / "USD" / "EUR" | enum |
| `budget_hidden` | Скрыть цену | Скрыть цену | q10 | true / false | boolean |
| `potential` | Потенциал/перспективы | Потенциал | q11 | "MRR $2k, растёт 10% m/m" | non_empty, max 500 |
| `traction` | Трекшен/метрики | Трекшен (опц.) | q12 | "10 платящих, 50 триалов" | optional, max 500 |
| `gtm_stage` | Стадия GTM | Стадия | q13 | "early_traction" / "growth" | non_empty |
| `goal_pub` | Цель публикации | Цель публикации | q14 | "Продажа" / "Партнёрство" | non_empty |
| `goal_inbound` | Готовность к inbound | Inbound готовность | q15 | "Готов к звонкам" | non_empty |
| `channels` | Каналы продвижения | Каналы (опц.) | q16 | ["telegram", "email"] | optional, array |
| `author_name` | Имя автора | Имя | q17 | "Иван Иванов" | non_empty, max 200 |
| `author_contact` | Контакт автора | Email/Telegram | q18 | "@ivan" | contact validator |
| `links` | Ссылки на проект | Ссылки | q19 | ["https://demo.com"] | array of URLs |

### Структура budget (q10)

Budget — композитный шаг, сохраняет несколько ключей:

```json
{
  "budget_min": 50000,
  "budget_max": 100000,
  "budget_currency": "RUB",
  "budget_hidden": false
}
```

**Варианты:**

1. Скрыта: `{ "budget_hidden": true }`
2. Фиксированная: `{ "budget_min": 50000, "budget_currency": "RUB" }`
3. Диапазон: `{ "budget_min": 50000, "budget_max": 100000, "budget_currency": "RUB" }`

---

## D) Маппинг Legacy → Unified

### Правило приоритета

При чтении данных из `answers`:

```text
1. Если есть новый V2 ключ → использовать его
2. Иначе fallback на legacy ключ
3. Если оба пусты → null/default
```

### Таблица маппинга

| UI Field | V2 Key (приоритет) | Legacy Key (fallback) | Transformation |
| ---------- | ------------------- | ---------------------- | ---------------- |
| **Title** | `title` + `subtitle` | `title` | Join with `\n` if both present |
| **Description** | `description` + `niche` + `what_done` + `status` | `description` | Join sections with `\n` |
| **Stack** | `stack_reason` | `stack` | Direct use |
| **Link** | `links[0]` | `link` | First element of array or string |
| **Price** | `budget_min`/`budget_max`/`budget_currency`/`budget_hidden` | `cost`/`cost_max`/`currency` | See price formatting |
| **Contact** | `author_contact` | `contact` | Direct use |

### Примеры маппинга

#### Title

```javascript
// V2
function getTitle(answers) {
  const title = answers.title || "";
  const subtitle = answers.subtitle || "";
  if (title && subtitle) return `${title}\n${subtitle}`;
  return title || subtitle || "—";
}
```

#### Price Display

```javascript
function getPriceDisplay(answers) {
  // V2 budget keys (приоритет)
  if (answers.budget_hidden === true) return "скрыта";
  
  const min = answers.budget_min ?? answers.cost;
  const max = answers.budget_max ?? answers.cost_max;
  const cur = answers.budget_currency || answers.currency || "RUB";
  
  // Legacy: currency === "HIDDEN"
  if (cur === "HIDDEN") return "скрыта";
  
  const symbol = cur === "USD" ? "$" : cur === "EUR" ? "€" : "₽";
  
  if (min && max && min !== max) {
    return `${formatNumber(min)}–${formatNumber(max)} ${symbol}`;
  }
  if (min) return `${formatNumber(min)} ${symbol}`;
  if (max) return `до ${formatNumber(max)} ${symbol}`;
  
  return "—";
}
```

#### Links

```javascript
function getPrimaryLink(answers) {
  // V2: array
  if (Array.isArray(answers.links) && answers.links.length > 0) {
    return answers.links[0];
  }
  // Legacy: string
  return answers.link || null;
}
```

---

## E) Preview == Published Rule

### Принцип

**Единый рендерер** для preview и publish:

```text
render_post(answers, mode="preview") → header + body
render_post(answers, mode="publish") → body only

body одинаковый в обоих случаях!
```

### Поля, участвующие в рендере

```typescript
const RENDER_SECTIONS = [
  { emoji: "🟢", key: "title" },        // title + subtitle
  { emoji: "📝", key: "description" },  // description + niche + what_done + status
  { emoji: "⚙️ Стек", key: "stack" },   // stack_reason
  { emoji: "🔗 Ссылка", key: "link" },  // links[0]
  { emoji: "💰 Цена", key: "price" },   // formatted from budget_*
  { emoji: "📬 Контакт", key: "contact" } // author_contact
];
```

### Consistency Check

Backend вызывает `assert_preview_publish_consistency()` при publish:

```python
def assert_preview_publish_consistency(answers: dict, publish_text: str):
    expected = render_post(answers, mode="publish")["text"]
    if publish_text != expected:
        raise AssertionError("Preview/publish mismatch")
```

### Frontend Rule

```typescript
// ПРАВИЛЬНО: использовать один и тот же компонент
<ProjectPostPreview answers={answers} />  // preview
<ProjectPostPublished answers={answers} /> // ❌ НЕ СОЗДАВАТЬ ОТДЕЛЬНЫЙ!

// ПРАВИЛЬНО:
<ProjectPost answers={answers} mode="preview" />
<ProjectPost answers={answers} mode="publish" />
// Оба рендерят одинаковый body
```

---

## F) Status Lifecycle и разрешённые действия

### Диаграмма переходов

```text
                    ┌──────────────┐
                    │    DRAFT     │
                    └──────┬───────┘
                           │ submit
                           ▼
                    ┌──────────────┐
           ┌────────│   PENDING    │────────┐
           │        └──────────────┘        │
           │ needs_fix              approve │
           ▼                                ▼
    ┌──────────────┐                ┌──────────────┐
    │  NEEDS_FIX   │                │   APPROVED   │
    └──────┬───────┘                └──────────────┘
           │ re-submit                      
           │ (revision++)                   
           └──────────► PENDING             
                                            
    ┌──────────────┐                        
    │   REJECTED   │ ← reject from PENDING  
    └──────────────┘                        
```

### Матрица действий

| Status | User Actions | Admin Actions | UI State |
| -------- | -------------- | --------------- | ---------- |
| **DRAFT** | edit, submit, delete | — | Badge: "Черновик", CTA: "Продолжить" |
| **PENDING** | view (readonly) | approve, needs_fix, reject | Badge: "На модерации", CTA: "Ожидайте" |
| **NEEDS_FIX** | edit, re-submit | — | Badge: "Требует правок", CTA: "Исправить" |
| **APPROVED** | view, archive | — | Badge: "Опубликован", CTA: "Посмотреть" |
| **REJECTED** | view, clone (create new) | — | Badge: "Отклонён", CTA: "—" |

### API Actions Matrix

| Endpoint | DRAFT | PENDING | NEEDS_FIX | APPROVED | REJECTED |
| ---------- | ------- | --------- | ----------- | ---------- | ---------- |
| `PUT /projects/{id}` | ✓ | ✗ 403 | ✓ | ✗ 403 | ✗ 403 |
| `POST /projects/{id}/submit` | ✓ | ✗ 403 | ✓ | ✗ 403 | ✗ 403 |
| `POST /projects/{id}/preview` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `POST /projects/{id}/archive` | ✓ | ✗ 403 | ✓ | ✓ | ✗ 403 |
| `DELETE /projects/{id}` | ✓ | ✗ 403 | ✗ 403 | ✗ 403 | ✗ 403 |

### Revision Strategy

```text
1. Создание: revision = 0, status = DRAFT
2. Первый submit: revision = 1, status = PENDING, submitted_at = now()
3. needs_fix: status = NEEDS_FIX, fix_request = "..."
4. Re-submit после правок: revision++, status = PENDING, submitted_at = now()
5. approve: status = APPROVED, moderated_at = now()
```

### UI Badge Colors

```typescript
const STATUS_BADGES = {
  draft: { color: "gray", label: "Черновик" },
  pending: { color: "yellow", label: "На модерации" },
  needs_fix: { color: "orange", label: "Требует правок" },
  approved: { color: "green", label: "Опубликован" },
  rejected: { color: "red", label: "Отклонён" }
};
```

---

## G) Versioning

### API Version Header

Все ответы API содержат заголовок:

```text
X-API-Version: v1
```

И опциональное поле в body:

```json
{
  "api_version": "v1",
  "data": { ... }
}
```

### answers Schema Version

`answers` может содержать meta-ключ:

```json
{
  "_schema_version": "2",
  "title": "...",
  ...
}
```

**Версии схемы:**

- `1` (legacy): 6 ключей (title, description, stack, link, price, contact)
- `2` (current): 19 ключей (title, subtitle, niche, ..., links)

### Migration Strategy

При чтении данных:

```python
def normalize_answers(answers: dict) -> dict:
    version = answers.get("_schema_version", "1")
    
    if version == "1":
        # Migrate legacy keys
        return migrate_v1_to_v2(answers)
    
    return answers

def migrate_v1_to_v2(answers: dict) -> dict:
    """Migrate legacy 6-key answers to V2 schema."""
    return {
        "_schema_version": "2",
        "title": answers.get("title", ""),
        "description": answers.get("description", ""),
        "contact": answers.get("contact", ""),
        "author_contact": answers.get("contact", ""),  # duplicate for V2
        "stack_reason": answers.get("stack", ""),
        "links": [answers.get("link")] if answers.get("link") else [],
        # Price migration
        "budget_min": parse_price_min(answers.get("price")),
        "budget_max": parse_price_max(answers.get("price")),
        "budget_currency": "RUB",
        # Остальные V2 поля — пустые
        "subtitle": "",
        "niche": "",
        "what_done": "",
        "status": "",
        "time_spent": "",
        "potential": "",
        "traction": "",
        "gtm_stage": "",
        "goal_pub": "",
        "goal_inbound": "",
        "channels": [],
        "author_name": "",
    }
```

### Breaking Changes Policy

1. **Новые поля** — добавляются как optional с default
2. **Переименование ключей** — поддерживать оба ключа минимум 2 версии
3. **Удаление ключей** — deprecation warning за 1 версию, удаление в следующей
4. **Изменение типов** — недопустимо; создавать новый ключ

---

## H) Type Definitions (TypeScript)

Полный набор типов для фронтенда:

```typescript
// === Enums ===
type ProjectStatus = "draft" | "pending" | "needs_fix" | "approved" | "rejected";
type LeadType = "PROJECT_INTEREST" | "REQUEST_OFFER";
type Currency = "RUB" | "USD" | "EUR";
type InputType = "text" | "textarea" | "select" | "multi_choice" | "links" | "budget";

// === answers JSON ===
interface ProjectAnswers {
  _schema_version?: "1" | "2";
  
  // Core (V1 compatible)
  title: string;
  description: string;
  contact: string;
  
  // V2 Extended
  subtitle?: string;
  niche?: string;
  what_done?: string;
  status?: string;
  stack_reason?: string;
  time_spent?: string;
  
  // Budget
  budget_min?: number;
  budget_max?: number;
  budget_currency?: Currency;
  budget_hidden?: boolean;
  
  // Legacy budget (fallback)
  cost?: string;
  cost_max?: string;
  currency?: string;
  
  // GTM
  potential?: string;
  traction?: string;
  gtm_stage?: string;
  
  // Goals
  goal_pub?: string;
  goal_inbound?: string;
  channels?: string[];
  
  // Author
  author_name?: string;
  author_contact?: string;
  
  // Links
  links?: string[];
  link?: string;  // Legacy
}

// === API Response Wrappers ===
interface ApiResponse<T> {
  api_version: string;
  data: T;
}

interface PaginatedResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}
```

---

## I) Validation Rules Summary

| Field | Type | Required | Min | Max | Pattern/Format |
| ------- | ------ | ---------- | ----- | ----- | ---------------- |
| title | string | ✓ | 1 | 200 | — |
| description | string | ✓ | 1 | 1000 | — |
| contact | string | ✓ | 1 | 200 | @username / email / phone |
| subtitle | string | ✗ | 0 | 200 | — |
| niche | string | ✓ | 1 | 200 | — |
| what_done | string | ✓ | 1 | 500 | — |
| status | string | ✓ | 1 | 100 | — |
| stack_reason | string | ✗ | 0 | 500 | — |
| time_spent | string | ✓ | 1 | 100 | "X месяцев/недель/лет" |
| budget_min | number | ✗ | 0 | 999999999 | integer |
| budget_max | number | ✗ | budget_min | 999999999 | integer |
| budget_currency | enum | ✗ | — | — | RUB/USD/EUR |
| budget_hidden | boolean | ✗ | — | — | true/false |
| potential | string | ✓ | 1 | 500 | — |
| traction | string | ✗ | 0 | 500 | — |
| gtm_stage | string | ✓ | 1 | 100 | — |
| goal_pub | string | ✓ | 1 | 200 | — |
| goal_inbound | string | ✓ | 1 | 200 | — |
| channels | array | ✗ | 0 | 10 | string[] |
| author_name | string | ✓ | 1 | 200 | — |
| author_contact | string | ✓ | 1 | 200 | @username / email |
| links | array | ✗ | 0 | 10 | valid URLs |

---

## J) Quick Reference

### Required Fields for Submit

Минимальный набор для отправки на модерацию:

```text
title, description, contact, subtitle, niche, what_done, 
status, time_spent, potential, gtm_stage, goal_pub, 
goal_inbound, author_name, author_contact
```

Optional: `stack_reason`, `traction`, `channels`, `links`, `budget_*`

### Status Transitions Cheatsheet

```text
DRAFT    → submit()  → PENDING
PENDING  → approve() → APPROVED
PENDING  → needsFix()→ NEEDS_FIX
PENDING  → reject()  → REJECTED
NEEDS_FIX→ submit()  → PENDING (revision++)
```

### Price Display Logic

```text
budget_hidden=true       → "скрыта"
budget_min + budget_max  → "50 000–100 000 ₽"
budget_min only          → "50 000 ₽"
budget_max only          → "до 100 000 ₽"
empty                    → "—"
```

---

## K) DTO Derived Fields & Access Control (расширение секции B)

### Универсальные derived-поля для всех DTO

Каждый DTO, связанный с проектом/черновиком, должен включать следующие вычисляемые поля:

```typescript
interface DerivedProjectFields {
  // Progress
  completion_percent: number;      // 0..100: (filled_required_fields / total_required_fields) * 100
  missing_fields: string[];        // answer_keys, которые пусты но required
  
  // Action hints
  next_action: NextActionDTO;      // Что делать пользователю
  
  // Access control (boolean flags)
  can_edit: boolean;               // Можно редактировать
  can_submit: boolean;             // Можно отправить на модерацию
  can_archive: boolean;            // Можно архивировать
  can_delete: boolean;             // Можно удалить
  can_clone: boolean;              // Можно клонировать
}

interface NextActionDTO {
  action: "continue" | "fix" | "wait" | "view" | "resubmit" | "none";
  label: string;                   // "Продолжить заполнение", "Внести правки", ...
  cta_enabled: boolean;            // Кнопка активна
  cta_url?: string;                // Deep link (если нужен)
}
```

### Access Control Matrix (can_* flags)

| Status | can_edit | can_submit | can_archive | can_delete | can_clone |
| -------- | ---------- | ------------ | ------------- | ------------ | ----------- |
| **DRAFT** | ✓ | ✓ (если complete) | ✓ | ✓ | ✗ |
| **PENDING** | ✗ | ✗ | ✗ | ✗ | ✗ |
| **NEEDS_FIX** | ✓ | ✓ (после fix) | ✗ | ✗ | ✗ |
| **APPROVED** | ✗ | ✗ | ✓ | ✗ | ✓ |
| **REJECTED** | ✗ | ✗ | ✗ | ✗ | ✓ |

### Логика вычисления can_submit

```typescript
function canSubmit(project: ProjectDetailsDTO): boolean {
  // 1. Status check
  if (!["draft", "needs_fix"].includes(project.status)) return false;
  
  // 2. Completion check
  if (project.missing_fields.length > 0) return false;
  
  // 3. All required fields filled
  return true;
}
```

### Расширенные DTO с derived fields

#### ProjectListItemDTO (полная версия)

```typescript
interface ProjectListItemDTO {
  // Identity
  id: string;
  status: ProjectStatus;
  revision: number;
  
  // Display
  title_short: string;           // truncated 50 chars
  niche_tag: string | null;      // answers.niche (первое слово)
  
  // Progress  
  completion_percent: number;    // 0..100
  missing_fields: string[];      // field_ids
  
  // Action
  next_action: NextActionDTO;
  
  // Access
  can_edit: boolean;
  can_submit: boolean;
  can_archive: boolean;
  can_delete: boolean;
  can_clone: boolean;
  
  // Timestamps
  created_at: string;
  updated_at: string;
  submitted_at: string | null;
  
  // Moderation
  has_fix_request: boolean;
  fix_request_preview: string | null;  // first 100 chars
}
```

#### ProjectDetailsDTO (полная версия)

```typescript
interface ProjectDetailsDTO {
  // Identity
  id: string;
  status: ProjectStatus;
  revision: number;
  current_step: string | null;
  
  // Content
  answers: ProjectAnswersV2;     // Full answers object
  rendered_post: string | null;  // HTML preview
  
  // Progress
  completion_percent: number;
  missing_fields: string[];
  filled_fields: string[];       // для UI progress bar
  
  // Action
  next_action: NextActionDTO;
  
  // Access
  can_edit: boolean;
  can_submit: boolean;
  can_archive: boolean;
  can_delete: boolean;
  can_clone: boolean;
  
  // Moderation
  fix_request: string | null;
  moderated_at: string | null;
  moderator_comment: string | null;
  
  // Timestamps
  created_at: string;
  updated_at: string;
  submitted_at: string | null;
}
```

#### PublicProjectCardDTO (полная версия)

```typescript
interface PublicProjectCardDTO {
  // Identity
  id: string;
  
  // Display
  title: string;
  subtitle: string | null;
  description_short: string;     // 200 chars max
  niche: string;
  what_done_short: string;       // 100 chars max
  
  // Price
  price_display: string;         // "50 000 ₽" | "скрыта" | "—"
  price_min: number | null;
  price_max: number | null;
  currency: Currency;
  
  // Author
  author_name: string;
  author_contact_masked: string; // "@us***" для каталога
  
  // Links
  primary_link: string | null;
  links_count: number;
  
  // Tags
  tags: string[];                // [niche, stack_ai?, status]
  
  // Meta
  created_at: string;
  published_at: string;          // когда approved
  
  // Derived (для UI)
  is_new: boolean;               // published < 7 days ago
  has_demo: boolean;             // links содержит demo/video
}
```

#### RequestDTO (полная версия)

```typescript
interface RequestDTO {
  // Identity
  id: string;
  buyer_telegram_id: number;     // External key (см. секцию L)
  
  // Content
  what: string;
  budget: string;
  contact: string;
  
  // Derived
  matched_projects_count: number;
  has_new_matches: boolean;      // есть непросмотренные
  
  // Access
  can_edit: boolean;             // true если owner
  can_delete: boolean;
  
  // Timestamps
  created_at: string;
  updated_at: string;
}
```

#### LeadDTO (полная версия)

```typescript
interface LeadDTO {
  // Identity
  id: string;
  lead_type: LeadType;
  
  // Project reference
  project_id: string;
  project_title: string;
  project_status: ProjectStatus;
  
  // Buyer info
  buyer: {
    telegram_id: number;         // External key
    username: string | null;
    full_name: string | null;
    contact_revealed: boolean;   // seller saw contact
  };
  
  // Request reference (если есть)
  request_id: string | null;
  request_preview: string | null; // first 100 chars
  
  // Status
  is_new: boolean;               // seller hasn't seen
  viewed_at: string | null;
  
  // Derived
  can_respond: boolean;          // true если есть контакт
  
  // Timestamps
  created_at: string;
}
```

---

## L) V2 Extended answers JSON Keys Registry (канонический реестр)

### Полная таблица V2 ключей

| json_key | meaning | ui_label | required | step_id | validation | example |
| ---------- | --------- | ---------- | ---------- | --------- | ------------ | --------- |
| `author_name` | Имя автора проекта | Ваше имя | yes | q17 | non_empty, max 200 | "Иван Петров" |
| `author_contact_mode` | Способ связи | Как с вами связаться | yes | q18 | enum: telegram/email/phone | "telegram" |
| `author_contact_value` | Значение контакта | Telegram / Email / Телефон | yes | q18 | depends on mode | "@ivanpetrov" |
| `role` | Роль автора в проекте | Ваша роль | no | q17 | max 100 | "Основатель, CTO" |
| `project_title` | Название проекта | Название проекта | yes | q1 | non_empty, max 200 | "AI-помощник для HR" |
| `project_subtitle` | Краткий слоган | Подзаголовок / Слоган | no | q1 | max 200 | "Автоматизация найма за 5 минут" |
| `problem` | Проблема, которую решает | Какую проблему решает | yes | q2 | non_empty, max 500 | "HR тратят 80% времени на скрининг" |
| `audience_type` | Целевая аудитория | Для кого этот продукт | yes | q5 | non_empty, max 200 | "B2B, HR-отделы от 10 человек" |
| `niche` | Ниша / Индустрия | Ниша | yes | q5 | non_empty, max 200 | "HR-tech, рекрутинг" |
| `what_done` | Что уже сделано | Что сделано | yes | q6 | non_empty, max 500 | "MVP, 10 платящих клиентов" |
| `project_status` | Текущий статус продукта | Стадия | yes | q7 | enum | "working_product" |
| `stack_ai` | AI/ML компоненты | AI/ML стек | no | q8 | max 300 | "GPT-4, LangChain, RAG" |
| `stack_tech` | Основной технический стек | Технологии | no | q8 | max 300 | "Python, FastAPI, React" |
| `stack_infra` | Инфраструктура | Инфра | no | q8 | max 300 | "AWS, Docker, PostgreSQL" |
| `stack_reason` | Почему выбран этот стек | Почему этот стек | no | q8 | max 500 | "Быстрый старт, много готовых решений" |
| `dev_time` | Время на разработку | Время разработки | yes | q9 | time_format | "6 месяцев" |
| `cost_currency` | Валюта цены | Валюта | yes (если цена не скрыта) | q10 | enum: RUB/USD/EUR | "RUB" |
| `cost_amount` | Цена (мин) | Цена | no | q10 | number >= 0 | 150000 |
| `cost_max` | Цена (макс, для диапазона) | Цена до | no | q10 | number >= cost_amount | 300000 |
| `cost_hidden` | Скрыть цену | Скрыть цену | no | q10 | boolean | false |
| `monetization_format` | Формат монетизации | Модель монетизации | no | q11 | enum | "subscription" |
| `monetization_text` | Описание монетизации | Как зарабатывает | no | q11 | max 500 | "Подписка $99/мес" |
| `potential` | Потенциал / Перспективы | Потенциал | yes | q11 | non_empty, max 500 | "TAM $5B, растём 20% m/m" |
| `goal` | Цель публикации | Зачем публикуете | yes | q14 | enum | "sale" |
| `inbound_ready` | Готовность к входящим | Готовность к звонкам | yes | q15 | non_empty, max 200 | "Готов к звонкам и демо" |
| `links` | Ссылки на проект | Ссылки | no | q19 | array of URLs, max 10 | ["https://demo.com"] |
| `cool_part` | Что крутого в проекте | Чем гордитесь | no | q12 | max 500 | "Уникальный алгоритм матчинга" |
| `hardest_part` | Что было сложнее всего | Главная сложность | no | q12 | max 500 | "Интеграция с 15 ATS" |
| `current_step` | Текущий шаг визарда | — | no | — | step_key | "q5" |
| `_meta.submission_state` | Внутренний статус отправки | — | no | — | internal | "submitted" |
| `_schema_version` | Версия схемы | — | no | — | "1" / "2" | "2" |

### Enum-значения

#### project_status

| value | ui_label |
| ------- | ---------- |
| `idea` | Идея |
| `prototype` | Прототип |
| `mvp` | MVP |
| `working_product` | Работающий продукт |
| `scaling` | Масштабирование |

#### monetization_format

| value | ui_label |
| ------- | ---------- |
| `subscription` | Подписка |
| `one_time` | Разовая покупка |
| `freemium` | Freemium |
| `ads` | Реклама |
| `marketplace` | Комиссия (маркетплейс) |
| `other` | Другое |

#### goal (цель публикации)

| value | ui_label |
| ------- | ---------- |
| `sale` | Продажа |
| `investment` | Инвестиции |
| `partnership` | Партнёрство |
| `team` | Поиск команды |
| `feedback` | Обратная связь |

#### author_contact_mode

| value | ui_label | validation |
| ------- | ---------- | ------------ |
| `telegram` | Telegram | @username or t.me/ link |
| `email` | Email | valid email format |
| `phone` | Телефон | phone number format |

### Группировка по блокам (для UI)

```typescript
const ANSWER_BLOCKS = {
  author: {
    emoji: "👤",
    label: "Автор",
    keys: ["author_name", "role", "author_contact_mode", "author_contact_value"]
  },
  project: {
    emoji: "📌",
    label: "Проект", 
    keys: ["project_title", "project_subtitle", "problem", "audience_type", "niche"]
  },
  done: {
    emoji: "✅",
    label: "Что сделано",
    keys: ["what_done", "project_status"]
  },
  stack: {
    emoji: "⚙️",
    label: "Стек",
    keys: ["stack_ai", "stack_tech", "stack_infra", "stack_reason"]
  },
  economics: {
    emoji: "💰",
    label: "Экономика",
    keys: ["dev_time", "cost_currency", "cost_amount", "cost_max", "cost_hidden", 
           "monetization_format", "monetization_text", "potential"]
  },
  highlights: {
    emoji: "⭐",
    label: "Особенности",
    keys: ["cool_part", "hardest_part"]
  },
  goals: {
    emoji: "🎯",
    label: "Цели",
    keys: ["goal", "inbound_ready"]
  },
  links: {
    emoji: "🔗",
    label: "Ссылки",
    keys: ["links"]
  }
};
```

---

## M) Legacy Mapping (расширение секции D)

### Правило приоритета V2 → V1

```text
При чтении данных из answers:
1. Сначала ищем V2 ключ
2. Если V2 ключ пуст/отсутствует — fallback на V1 ключ
3. Если оба пусты — возвращаем null / default value
```

### Таблица маппинга V2 ↔ V1

| Field | V2 Key (primary) | V1 Key (fallback) | Transform |
| ------- | ------------------ | ------------------- | ----------- |
| **Title** | `project_title` | `title` | direct |
| **Subtitle** | `project_subtitle` | `subtitle` | direct |
| **Description** | `problem` | `description` | direct |
| **Niche** | `niche` | — | — |
| **What Done** | `what_done` | — | — |
| **Status** | `project_status` | `status` | direct |
| **Stack** | `stack_tech + stack_ai + stack_infra` | `stack` / `stack_reason` | join with ", " |
| **Price Min** | `cost_amount` | `budget_min` / `cost` | number |
| **Price Max** | `cost_max` | `budget_max` | number |
| **Currency** | `cost_currency` | `budget_currency` / `currency` | direct |
| **Price Hidden** | `cost_hidden` | `budget_hidden` | boolean |
| **Contact** | `author_contact_value` | `author_contact` / `contact` | direct |
| **Contact Mode** | `author_contact_mode` | — | infer from value |
| **Author Name** | `author_name` | — | — |
| **Links** | `links` | `link` (string→array) | wrap in array |
| **Potential** | `potential` | — | — |
| **Goal** | `goal` | `goal_pub` | direct |
| **Inbound** | `inbound_ready` | `goal_inbound` | direct |

### Примеры маппинга (Extended)

```typescript
// Title: V2 → V1 fallback
function getTitle(answers: Partial<ProjectAnswersV2>): string {
  return answers.project_title 
      || answers.title 
      || "—";
}

// Stack: composite field
function getStack(answers: Partial<ProjectAnswersV2>): string {
  const parts = [
    answers.stack_ai,
    answers.stack_tech,
    answers.stack_infra
  ].filter(Boolean);
  
  if (parts.length > 0) return parts.join(", ");
  
  // V1 fallback
  return answers.stack_reason || answers.stack || "—";
}

// Contact: V2 → V1 fallback
function getContact(answers: Partial<ProjectAnswersV2>): string {
  if (answers.author_contact_value) {
    return answers.author_contact_value;
  }
  return answers.author_contact || answers.contact || "—";
}

// Links: normalize to array
function getLinks(answers: Partial<ProjectAnswersV2>): string[] {
  if (Array.isArray(answers.links) && answers.links.length > 0) {
    return answers.links;
  }
  // V1: single link string
  if (answers.link) {
    return [answers.link];
  }
  return [];
}
```

---

## N) Preview == Published (расширение секции E)

### Принцип единого рендерера

```text
ОДНА функция render_post() для:
- Preview в редакторе (mode="preview")
- Feed-пост в канале (mode="publish")  
- Карточка в каталоге (mode="card")

Результат ИДЕНТИЧЕН для preview и publish!
```

### Единый формат поста

```typescript
interface RenderedPost {
  text: string;          // Plain text / HTML
  entities?: Entity[];   // Telegram entities (bold, italic, links)
  photo_url?: string;    // OG-image если есть
}

function renderPost(
  answers: ProjectAnswersV2, 
  mode: "preview" | "publish" | "card"
): RenderedPost {
  // Одинаковая логика для preview и publish
  const sections = buildSections(answers);
  
  if (mode === "card") {
    return { text: renderCardFormat(sections) };
  }
  
  // preview и publish используют ОДИН формат
  return { text: renderFullFormat(sections) };
}
```

### Поля, участвующие в рендере (Extended)

| Section | Keys Used | Emoji | Order |
| --------- | ----------- | ------- | ------- |
| Title | `project_title`, `project_subtitle` | 🟢 | 1 |
| Problem | `problem`, `audience_type`, `niche` | 📝 | 2 |
| What Done | `what_done`, `project_status` | ✅ | 3 |
| Stack | `stack_ai`, `stack_tech`, `stack_infra` | ⚙️ | 4 |
| Economics | `cost_*`, `monetization_*`, `potential` | 💰 | 5 |
| Links | `links[0]` | 🔗 | 6 |
| Contact | `author_name`, `author_contact_value` | 📬 | 7 |

### Consistency Check (Extended)

```python
def ensure_preview_publish_match(submission: Submission) -> None:
    """
    Вызывается при submit.
    Гарантирует что rendered_post == то что пойдёт в feed.
    """
    preview_html = render_post(submission.answers, mode="preview").text
    publish_html = render_post(submission.answers, mode="publish").text
    
    # Должны совпадать (кроме header в preview)
    assert normalize(preview_html) == normalize(publish_html), \
        "Preview/Publish mismatch — fix render_post()"
```

### Frontend: один компонент

```typescript
// ✓ ПРАВИЛЬНО: один компонент с mode prop
<ProjectPost answers={answers} mode="preview" />
<ProjectPost answers={answers} mode="publish" />

// ✗ НЕПРАВИЛЬНО: разные компоненты
<ProjectPreviewCard answers={answers} />
<ProjectPublishCard answers={answers} />
```

---

## O) User Identity Rules (правило идентификаторов)

### Telegram ID как внешний ключ

```text
┌─────────────────────────────────────────────────────────────┐
│  API / Frontend используют telegram_id как внешний ключ    │
│  User.id — internal PK, НИКОГДА не отдаётся наружу         │
└─────────────────────────────────────────────────────────────┘
```

### Правила

| Context | Use | Never Use |
| --------- | ----- | ----------- |
| API auth header | `X-Telegram-User-Id: 123456` | User.id |
| API response | `{ "telegram_id": 123456 }` | `{ "user_id": 1 }` |
| Frontend storage | `telegram_id` | internal id |
| Logs (public) | `tg_id=123456` | `user_id=1` |
| DB queries (internal) | `User.id` for FK | — |

### Пример API response

```json
// ✓ ПРАВИЛЬНО
{
  "data": {
    "project": { "id": "uuid-..." },
    "owner": {
      "telegram_id": 123456789,
      "username": "ivan_dev",
      "full_name": "Иван Петров"
    }
  }
}

// ✗ НЕПРАВИЛЬНО  
{
  "data": {
    "project": { "id": "uuid-...", "user_id": 42 },
    "owner_id": 42
  }
}
```

### Auth Flow

```text
1. Mini App получает initData от Telegram
2. Backend валидирует initData.user.id
3. Backend ищет User WHERE telegram_id = initData.user.id
4. Если нет — создаёт User с telegram_id
5. Все дальнейшие запросы используют telegram_id
6. Internal User.id используется только в JOIN-ах внутри БД
```

### TypeScript types

```typescript
// API types — только telegram_id
interface UserPublicDTO {
  telegram_id: number;           // ← external key
  username: string | null;
  full_name: string | null;
}

// Internal types (backend only)
interface UserInternal {
  id: number;                    // ← internal PK, never exposed
  telegram_id: number;
  // ...
}
```

---

## P) Summary: Required Fields for Submit (V2)

### Минимальный набор для отправки на модерацию

**Обязательные (14 полей):**

```text
project_title, problem, audience_type, niche, 
what_done, project_status, dev_time, potential, 
goal, inbound_ready, author_name, 
author_contact_mode, author_contact_value
```

**Условно обязательные:**

- `cost_currency` + `cost_amount` — если `cost_hidden != true`

**Опциональные:**

```text
project_subtitle, role, stack_ai, stack_tech, stack_infra, 
stack_reason, cost_max, monetization_format, monetization_text,
cool_part, hardest_part, links
```

### Validation на submit

```typescript
const REQUIRED_FOR_SUBMIT: string[] = [
  "project_title",
  "problem", 
  "audience_type",
  "niche",
  "what_done",
  "project_status",
  "dev_time",
  "potential",
  "goal",
  "inbound_ready",
  "author_name",
  "author_contact_mode",
  "author_contact_value"
];

function validateForSubmit(answers: Partial<ProjectAnswersV2>): string[] {
  const missing: string[] = [];
  
  for (const key of REQUIRED_FOR_SUBMIT) {
    const value = answers[key];
    if (value === undefined || value === null || value === "") {
      missing.push(key);
    }
  }
  
  // Conditional: price required if not hidden
  if (!answers.cost_hidden) {
    if (!answers.cost_currency) missing.push("cost_currency");
    if (!answers.cost_amount && answers.cost_amount !== 0) missing.push("cost_amount");
  }
  
  return missing;
}
```

---

## B) DTO models (для Mini App UI)

> Принцип: API/Frontend работают с DTO, а не с ORM-моделями.  
> Внешний идентификатор пользователя для API — telegram_id. User.id (internal) наружу не отдаём.

### B1) ProjectListItemDTO (Мои проекты — список)

Используется на экране "Projects".

| Field | Type | Nullable | Notes |
| --- | --- | ---: | --- |
| id | uuid | ✗ | submission id |
| title | string | ✗ | derived from answers (см. mapping) |
| subtitle | string | ✓ | short "what it is" |
| status | string | ✗ | ProjectStatus enum |
| revision | int | ✗ | current revision |
| updated_at | datetime | ✗ | |
| submitted_at | datetime | ✓ | |
| moderated_at | datetime | ✓ | |
| completion_percent | int | ✗ | 0..100 (derived) |
| next_action | string | ✗ | enum: CONTINUE_FORM / PREVIEW / SUBMIT / FIX / ARCHIVE |
| missing_fields | string[] | ✗ | list of canonical keys missing |
| can_edit | bool | ✗ | derived from status |
| can_submit | bool | ✗ | derived from status + completeness |
| can_archive | bool | ✗ | derived from status |

Rules

- completion_percent считается как (answered_required / required_total) * 100.
- next_action:
  - DRAFT → CONTINUE_FORM (если не все required) иначе PREVIEW
  - SUBMITTED → (нет действий, кроме VIEW)
  - NEEDS_FIX → FIX
  - APPROVED/REJECTED → ARCHIVE (или "Create new")

---

### B2) ProjectDetailsDTO (Детали проекта)

Экран "Project details" + "Preview".

| Field | Type | Nullable | Notes |
| --- | --- | ---: | --- |
| id | uuid | ✗ | |
| status | string | ✗ | |
| revision | int | ✗ | |
| current_step | string | ✓ | e.g. q1..q23 |
| answers | object | ✓ | raw answers JSON (admin-only or debug mode) |
| fields | ProjectFieldsDTO | ✗ | normalized fields for rendering |
| preview_html | string | ✓ | generated by renderer (HTML) |
| feed_html | string | ✓ | must equal preview_html for same answers |
| fix_request | string | ✓ | if NEEDS_FIX |
| created_at | datetime | ✗ | |
| updated_at | datetime | ✗ | |
| submitted_at | datetime | ✓ | |
| moderated_at | datetime | ✓ | |

---

### B3) ProjectFieldsDTO (нормализованные поля проекта)

Это "единая форма" данных, из которой рендерятся preview/publish.

| Field | Type | Nullable | Canonical source key |
| --- | --- | ---: | --- |
| author_name | string | ✗ | author_name |
| author_contact_mode | string | ✗ | author_contact_mode (telegram/email/other) |
| author_contact_value | string | ✗ | author_contact_value |
| author_role | string | ✗ | role |
| project_title | string | ✗ | project_title |
| project_subtitle | string | ✗ | project_subtitle |
| problem | string | ✗ | problem |
| audience_type | string | ✗ | audience_type |
| niche | string | ✓ | niche |
| what_done | string | ✗ | what_done |
| project_status_label | string | ✗ | project_status |
| stack_ai | string | ✗ | stack_ai |
| stack_tech | string | ✗ | stack_tech |
| stack_infra | string | ✗ | stack_infra |
| stack_reason | string | ✓ | stack_reason |
| dev_time | string | ✗ | dev_time |
| price | string | ✗ | derived from "pricing" mapping |
| monetization | string | ✗ | monetization_text + monetization_format |
| potential | string | ✓ | potential |
| goal | string | ✗ | goal |
| inbound_ready | string | ✗ | inbound_ready |
| links | string[] | ✓ | links |
| cool_part | string | ✗ | cool_part |
| hardest_part | string | ✗ | hardest_part |

---

### B4) PublicProjectCardDTO (Каталог)

| Field | Type | Nullable | Notes |
| --- | --- | ---: | --- |
| project_id | uuid | ✗ | derived: submission id (or future Project.id) |
| title | string | ✗ | |
| subtitle | string | ✓ | |
| niche | string | ✓ | |
| price_short | string | ✓ | derived |
| tags | string[] | ✓ | derived from niche/stack/audience |
| contact_hint | string | ✓ | e.g. "Telegram / Email" (not full contact) |
| published_at | datetime | ✓ | from moderated_at |
| feed_link | string | ✓ | optional link to channel post if tracked |

---

### B5) RequestDTO (Buyer Requests)

| Field | Type | Nullable |
| --- | --- | ---: |
| id | uuid | ✗ |
| buyer_telegram_id | int64 | ✗ |
| what | string | ✗ |
| budget | string | ✗ |
| contact | string | ✗ |
| created_at | datetime | ✗ |

---

### B6) LeadDTO

| Field | Type | Nullable |
| --- | --- | ---: |
| id | uuid | ✗ |
| lead_type | string | ✗ |
| project_id | uuid | ✗ |
| buyer_request_id | uuid | ✓ |
| created_at | datetime | ✗ |

---

## C) answers JSON keys registry (canonical)

> Принцип: ключи стабильны, не переименовывать без versioning.  
> Валидации указываются для UI/API.

Required keys (must for submit)

| json_key | meaning | ui_label | required | step_id | validation | example |
| --- | --- | --- | --- | --- | --- | --- |
| author_name | Имя/ник автора | Как тебя называть | yes | q1 | max_len 60 | "GoodLifeFM" |
| author_contact_mode | Тип контакта | Контакт: Telegram/Email | yes | q2 | enum | "telegram" |
| author_contact_value | Значение контакта | Контакт | yes | q2 | tg @... OR email regex | "@goodlifefm" |
| role | Роль | Твоя роль | yes | q3 | enum/str | "фаундер" |
| project_title | Название проекта | Название проекта | yes | q4 | max_len 80 | "VibeMarket" |
| project_subtitle | Коротко что это | Что это? | yes | q5 | max_len 200 | "AI-витрина проектов…" |
| problem | Проблема | Какую проблему решает | yes | q6 | max_len 600 | "У кого болит…" |
| audience_type | Тип аудитории | Для кого проект | yes | q7 | enum | "B2B" |
| what_done | Что реально сделано | Что работает сейчас | yes | q9 | max_len 1200 | "Генерация, CRM…" |
| project_status | Статус | Статус проекта | yes | q10 | enum | "MVP" |
| stack_ai | AI/LLM | AI/LLM | yes | q11 | max_len 200 | "GPT-4o, Claude" |
| stack_tech | Технологии | Backend/Frontend/No-code | yes | q12 | max_len 400 | "FastAPI, React…" |
| stack_infra | Инфра | Хостинг/БД/интеграции | yes | q13 | max_len 400 | "Docker, Postgres…" |
| dev_time | Время разработки | Сколько времени ушло | yes | q15 | must contain digit | "40 часов" |
| price_mode | Цена/стоимость режим | Стоимость | yes | q16 | enum | "RANGE" |
| price_value | Цена/стоимость значение | Стоимость | yes | q16 | string | "50–100k ₽" |
| monetization_format | Формат монетизации | Формат | yes | q17 | enum | "подписка" |
| monetization_text | Экономика проекта | За сколько/как | yes | q17 | max_len 300 | "от 20k/мес…" |
| goal | Цель | Зачем публикация | yes | q19 | enum | "найти клиентов" |
| inbound_ready | Готовность | Готов ли к входящим | yes | q20 | enum | "да" |
| cool_part | Самое крутое | Что самое крутое | yes | q22 | max_len 250 | "Сборка за 2 часа" |
| hardest_part | Самое сложное | Что было сложным | yes | q23 | max_len 400 | "Интеграции…" |

Optional keys

| json_key | meaning | ui_label | required | step_id | validation | example |
| --- | --- | --- | --- | --- | --- | --- |
| niche | Ниша | Ниша/сегмент | no | q8 | max_len 120 | "Юристы" |
| stack_reason | Почему стек | Почему так | no | q14 | max_len 250 | "быстро MVP" |
| potential | Потенциал | Потенциал | no | q18 | max_len 400 | "кому продать…" |
| links | Ссылки | Ссылки | no | q21 | url[] | ["https://…"] |
| _meta.project_submission_state | Текущий шаг FSM | meta | no | internal | string | "q12" |
| current_step | Текущий шаг (дубликат) | meta | no | internal | string | "q12" |

Notes

- links хранится как массив строк.
- price_mode и price_value — единый нормализованный формат цены (см. D).

---

## D) Legacy mapping + Preview == Published

### D1) Legacy mapping rules

Если встречаются старые ключи (V1), используется фолбэк.

Priority

1) Canonical V2 key (таблицы выше)
2) Legacy V1 key (если существует)
3) Empty

Examples

- title:
  - v2: project_title
  - v1 fallback: title
- subtitle/description:
  - v2: project_subtitle
  - v1 fallback: description
- stack:
  - v2: stack_ai, stack_tech, stack_infra
  - v1 fallback: stack (string)
- contact:
  - v2: author_name + author_contact_value
  - v1 fallback: contact
- links:
  - v2: links (array)
  - v1 fallback: link (string) → normalize to [link]
- price:
  - v2: price_mode + price_value
  - v1 fallback: cost/currency/cost_max → format string

### D2) Price normalization (single question)

Mini App использует единый формат (один вопрос в UI), но хранит нормализовано:

- price_mode enum:
  - FIXED (фиксированная сумма)
  - RANGE (диапазон)
  - NDA (не раскрываю)
  - FREE (бесплатно/опенсорс)
- price_value:
  - FIXED: "50000 ₽" or "$500"
  - RANGE: "50–100k ₽"
  - NDA: "не раскрываю"
  - FREE: "бесплатно"

UI может показывать один вопрос, но сохраняет два ключа.

### D3) Preview == Published (non-negotiable)

Правило: preview и публикация должны использовать один и тот же renderer и одни и те же normalized fields.

- source of truth: answers JSON
- normalized: ProjectFieldsDTO
- renderer output: HTML (Telegram parse_mode=HTML)

Guarantee:

- preview_html == feed_html для одинакового answers snapshot.

Если отличается — это баг.
