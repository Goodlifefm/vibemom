# Mini App API Specification

Version: 1.0  
Date: 2026-02-05  
Status: Production

---

## Overview

REST API service for Telegram Mini App, providing:
- Telegram WebApp authentication (initData validation + JWT tokens)
- Project management (list, details, preview)
- User information

Base URL: `http://localhost:8000` (development) or your production domain.

All responses include header: `X-API-Version: v1`

---

## Authentication

### POST /auth/telegram

Authenticate user with Telegram WebApp initData.

**Request:**

```http
POST /auth/telegram
Content-Type: application/json

{
  "initData": "query_id=AAH...&user=%7B%22id%22%3A123...&auth_date=1707123456&hash=abc123..."
}
```

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `initData` | string | Yes | Raw initData string from `window.Telegram.WebApp.initData` |

**Response (200 OK):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 2592000,
  "user": {
    "telegram_id": 123456789,
    "username": "johndoe",
    "full_name": "John Doe",
    "is_admin": false
  }
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `access_token` | string | JWT token for subsequent requests |
| `token_type` | string | Always "bearer" |
| `expires_in` | number | Token lifetime in seconds |
| `user.telegram_id` | number | Telegram user ID |
| `user.username` | string | Telegram @username (nullable) |
| `user.full_name` | string | User's display name |
| `user.is_admin` | boolean | Admin flag |

**Error Response (401 Unauthorized):**

```json
{
  "detail": "Invalid initData: Invalid hash signature"
}
```

**How to obtain initData:**

In your Telegram Mini App JavaScript:

```javascript
// Access initData from Telegram WebApp
const initData = window.Telegram.WebApp.initData;

// Send to API
const response = await fetch('https://api.example.com/auth/telegram', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ initData })
});

const { access_token } = await response.json();
// Store access_token for subsequent requests
```

---

## Authorization

All authenticated endpoints require Bearer token in Authorization header:

```http
Authorization: Bearer <access_token>
```

**Error Response (401 Unauthorized):**

```json
{
  "detail": "Missing authentication token"
}
```

or

```json
{
  "detail": "Token has expired"
}
```

---

## User Endpoints

### GET /me

Get current authenticated user's information.

**Request:**

```http
GET /me
Authorization: Bearer <access_token>
```

**Response (200 OK):**

```json
{
  "telegram_id": 123456789,
  "username": "johndoe",
  "full_name": "John Doe",
  "is_admin": false
}
```

---

## Project Endpoints

### GET /projects/my

Get list of all projects for the current user.

**Request:**

```http
GET /projects/my
Authorization: Bearer <access_token>
```

**Response (200 OK):**

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "draft",
    "revision": 0,
    "title_short": "AI-помощник для HR",
    "completion_percent": 65,
    "next_action": {
      "action": "continue",
      "label": "Продолжить заполнение",
      "cta_enabled": true
    },
    "can_edit": true,
    "can_submit": false,
    "can_archive": true,
    "can_delete": true,
    "created_at": "2026-02-05T10:00:00Z",
    "updated_at": "2026-02-05T12:30:00Z",
    "submitted_at": null,
    "has_fix_request": false,
    "fix_request_preview": null,
    "current_step": "q5",
    "missing_fields": ["potential", "goal", "inbound_ready"]
  }
]
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | string (UUID) | Project identifier |
| `status` | string | `draft`, `pending`, `needs_fix`, `approved`, `rejected` |
| `revision` | number | Revision number (increments on resubmit) |
| `title_short` | string | Truncated title (max 50 chars) |
| `completion_percent` | number | 0-100, based on required fields |
| `next_action.action` | string | `continue`, `fix`, `wait`, `view`, `archived` |
| `next_action.label` | string | UI label for next action |
| `next_action.cta_enabled` | boolean | Whether CTA button should be active |
| `can_edit` | boolean | User can edit project |
| `can_submit` | boolean | User can submit for moderation |
| `can_archive` | boolean | User can archive project |
| `can_delete` | boolean | User can delete project |
| `has_fix_request` | boolean | Has moderator feedback |
| `fix_request_preview` | string | First 100 chars of fix request |
| `current_step` | string | Current wizard step (q1-q23) |
| `missing_fields` | string[] | List of unfilled required field keys |

---

### GET /projects/{id}

Get full project details by ID.

**Request:**

```http
GET /projects/550e8400-e29b-41d4-a716-446655440000
Authorization: Bearer <access_token>
```

**Access Control:**
- Owner can view their own projects
- Admin can view any project

**Response (200 OK):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "draft",
  "revision": 0,
  "current_step": "q5",
  "answers": {
    "project_title": "AI-помощник для HR",
    "project_subtitle": "Автоматизация рекрутинга",
    "problem": "HR тратят 80% времени на скрининг резюме",
    "author_name": "Иван Петров",
    "author_contact_value": "@ivanpetrov"
  },
  "fields": {
    "author_name": "Иван Петров",
    "author_contact": "@ivanpetrov",
    "project_title": "AI-помощник для HR",
    "project_subtitle": "Автоматизация рекрутинга",
    "problem": "HR тратят 80% времени на скрининг резюме",
    "stack_ai": null,
    "stack_tech": null,
    "price_display": null,
    "links": []
  },
  "preview_html": "<b>🟢</b>\nAI-помощник для HR\nАвтоматизация рекрутинга\n\n<b>📝</b>\nHR тратят 80% времени на скрининг резюме\n\n<b>📬 Контакт</b>\nИван Петров\n@ivanpetrov",
  "completion_percent": 65,
  "missing_fields": ["potential", "goal", "inbound_ready"],
  "filled_fields": ["project_title", "problem", "author_name", "author_contact_value"],
  "next_action": {
    "action": "continue",
    "label": "Продолжить заполнение",
    "cta_enabled": true
  },
  "can_edit": true,
  "can_submit": false,
  "can_archive": true,
  "can_delete": true,
  "fix_request": null,
  "moderated_at": null,
  "created_at": "2026-02-05T10:00:00Z",
  "updated_at": "2026-02-05T12:30:00Z",
  "submitted_at": null
}
```

**Error Response (404 Not Found):**

```json
{
  "detail": "Project not found or access denied"
}
```

---

### POST /projects/{id}/preview

Generate HTML preview for a project.

**Request:**

```http
POST /projects/550e8400-e29b-41d4-a716-446655440000/preview
Authorization: Bearer <access_token>
```

**Response (200 OK):**

```json
{
  "preview_html": "<b>🟢</b>\nAI-помощник для HR\nАвтоматизация рекрутинга\n\n<b>📝</b>\nHR тратят 80% времени на скрининг резюме\n\n<b>📬 Контакт</b>\nИван Петров\n@ivanpetrov"
}
```

**Note:** Uses the same renderer as GET /projects/{id}, ensuring preview == published consistency.

---

## Health & Debug Endpoints

### GET /healthz

Health check endpoint.

**Request:**

```http
GET /healthz
```

**Response (200 OK):**

```json
{
  "status": "ok",
  "database": "ok"
}
```

**Response (503 Service Unavailable):**

```json
{
  "status": "unhealthy",
  "database": "unavailable"
}
```

---

### GET /version

Version and build information.

**Request:**

```http
GET /version
```

**Response (200 OK):**

```json
{
  "version": "1.0.0",
  "git_sha": "abc1234",
  "git_branch": "main",
  "build_time": "2026-02-05T10:00:00Z",
  "env": "local"
}
```

---

## Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 401 | Unauthorized - Missing or invalid token |
| 403 | Forbidden - Access denied |
| 404 | Not Found - Resource doesn't exist or access denied |
| 422 | Validation Error - Invalid request body |
| 500 | Internal Server Error |
| 503 | Service Unavailable - Database unreachable |

---

## Project Status Lifecycle

```
DRAFT → PENDING → NEEDS_FIX → PENDING (revision++) → APPROVED
                          ↘                       ↗
                            → → → REJECTED
```

| Status | Description | User Actions |
|--------|-------------|--------------|
| `draft` | Work in progress | Edit, Submit, Delete |
| `pending` | Awaiting moderation | View only |
| `needs_fix` | Requires changes | Edit, Resubmit |
| `approved` | Published | View, Archive |
| `rejected` | Declined | View, Clone |

---

## Required Fields for Submit

The following fields must be filled for submission:

```
project_title, problem, audience_type, niche, what_done, project_status,
dev_time, potential, goal, inbound_ready, author_name, 
author_contact_mode, author_contact_value
```

If `cost_hidden` is not true, also required:
- `cost_currency`
- `cost_amount`

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `BOT_TOKEN` | Telegram Bot Token (for initData validation) | Required |
| `API_JWT_SECRET` | JWT signing secret | `change-me-in-production` |
| `API_JWT_TTL_MIN` | Token lifetime in minutes | `43200` (30 days) |
| `WEBAPP_ORIGINS` | CORS allowed origins (comma-separated) | Empty |
| `ADMIN_IDS` | Admin Telegram IDs (comma-separated) | Empty |
| `LOG_LEVEL` | Logging level | `INFO` |
| `APP_ENV` | Environment (`local`, `production`) | `local` |

---

## Docker Commands

```bash
# Build and start API service
docker compose up -d --build api

# Check health
curl http://localhost:8000/healthz

# Check version
curl http://localhost:8000/version

# View logs
docker compose logs -f api
```

---

## Testing Authentication

### Development Testing

1. Create a Telegram Bot and get BOT_TOKEN
2. Set up a Mini App pointing to your frontend
3. In the Mini App, access `window.Telegram.WebApp.initData`
4. Send to `/auth/telegram` endpoint

### Manual Testing (Development Only)

For local development, you can generate test initData:

```python
import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

BOT_TOKEN = "your_bot_token"

user_data = {
    "id": 123456789,
    "first_name": "Test",
    "last_name": "User",
    "username": "testuser"
}

auth_date = int(time.time())
data = {
    "user": json.dumps(user_data),
    "auth_date": str(auth_date),
    "query_id": "test_query"
}

# Create data-check-string
data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))

# Create secret key
secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()

# Calculate hash
hash_value = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

data["hash"] = hash_value
init_data = urlencode(data)

print(init_data)
```

---

## OpenAPI Documentation

When `APP_ENV` is not `production`, Swagger UI is available at:
- `/docs` - Swagger UI
- `/redoc` - ReDoc

---

## Changelog

### v1.0.0 (2026-02-05)

- Initial release
- Authentication: POST /auth/telegram
- User: GET /me
- Projects: GET /projects/my, GET /projects/{id}, POST /projects/{id}/preview
- Health: GET /healthz, GET /version
