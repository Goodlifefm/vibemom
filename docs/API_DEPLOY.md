# API Deployment — api.vibemom.ru

Quick reference for deploying FastAPI backend with HTTPS.

## Domain & Ports

| Component | Value |
|-----------|-------|
| **API Domain** | `api.vibemom.ru` |
| **Nginx Ports** | `80` (HTTP → HTTPS redirect), `443` (HTTPS) |
| **Internal API** | `8000` (Docker network only) |
| **Database** | `5432` (Docker network only) |

## Required Environment Variables

**.env на VPS (обязательные):**

```env
# === ОБЯЗАТЕЛЬНЫЕ ===
BOT_TOKEN=<токен от BotFather>
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/vibe_market
API_JWT_SECRET=<длинная случайная строка 32+ символов>

# === РЕКОМЕНДУЕМЫЕ (для production) ===
APP_ENV=production
WEBAPP_URL=https://<vercel-app>.vercel.app
API_PUBLIC_URL=https://api.vibemom.ru
ALLOWED_ORIGINS=https://<vercel-app>.vercel.app,https://web.telegram.org,https://t.me

# === ОПЦИОНАЛЬНО ===
LOG_LEVEL=INFO
TG_INIT_DATA_SKIP_VERIFY=false  # НИКОГДА true в production!
```

**Vercel Environment Variables:**

```
VITE_API_PUBLIC_URL=https://api.vibemom.ru
```

## Quick Deploy Commands

```bash
# SSH на VPS
ssh root@<VPS_IP>
cd /root/vibemom

# Обновить код
git fetch && git checkout v2-editor && git pull

# Обновить .env
nano .env  # заполнить WEBAPP_URL, API_PUBLIC_URL, API_JWT_SECRET

# Production deploy (nginx + SSL)
make up-prod

# Или вручную:
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

## SSL Certificate

**Первый раз:**
```bash
make cert-issue DOMAIN=api.vibemom.ru EMAIL=your@email.com
```

**Продление:**
```bash
make cert-renew
```

## Health Check Commands

```bash
# После деплоя — проверить что API работает:

# 1. Внутренний (из VPS)
curl http://localhost:8000/healthz
# Ожидается: {"status":"ok","database":"ok"}

# 2. HTTPS (из интернета)
curl https://api.vibemom.ru/healthz
# Ожидается: {"status":"ok","database":"ok"}

# 3. Version endpoint
curl https://api.vibemom.ru/version
# Ожидается: {"version":"1.0.0","env":"production","webapp_url":"https://...","api_public_url":"https://..."}

# 4. CORS headers (должен быть Access-Control-Allow-Origin)
curl -I -H "Origin: https://web.telegram.org" https://api.vibemom.ru/healthz

# 5. Проверить env в контейнере
docker compose exec api printenv | grep -E "(WEBAPP_URL|API_PUBLIC_URL|ALLOWED_ORIGINS|APP_ENV)"
```

## API Endpoints (no auth required)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/healthz` | GET | Health check (DB connection) |
| `/version` | GET | Version info, env, URLs |
| `/` | GET | Service info |

## CORS Configuration

**Auto-included origins:**
- `http://localhost:5173` (dev)
- `http://127.0.0.1:5173` (dev)
- `https://web.telegram.org`
- `https://t.me`

**Regex patterns (auto-matched):**
- `https://*.vercel.app`
- `https://app.vibemom.ru`

**From env:**
- `WEBAPP_URL` (auto-normalized)
- `ALLOWED_ORIGINS` (comma-separated)

## Reverse Proxy

API работает за Nginx с SSL termination:

```
Browser/Telegram → Nginx:443 (HTTPS) → API:8000 (HTTP internal)
```

Nginx передаёт заголовки:
- `X-Real-IP`
- `X-Forwarded-For`
- `X-Forwarded-Proto`
- `X-Forwarded-Host`

Uvicorn настроен доверять proxy headers: `--forwarded-allow-ips *`

## Troubleshooting

**API не отвечает:**
```bash
docker compose ps  # проверить что api running
docker compose logs api --tail=50  # смотреть ошибки
```

**CORS ошибки:**
```bash
docker compose logs api | grep "CORS enabled"  # увидеть разрешённые origins
```

**SSL не работает:**
```bash
make cert-status  # статус сертификата
docker compose logs nginx --tail=30  # ошибки nginx
```

**Database unavailable:**
```bash
docker compose ps db  # проверить что db healthy
docker compose logs db --tail=30  # ошибки postgres
```

## Files Reference

| File | Purpose |
|------|---------|
| `services/api/Dockerfile` | API container config |
| `services/api/app/main.py` | FastAPI app, CORS, middleware |
| `services/api/app/config.py` | Settings, env vars |
| `services/api/app/routers/health.py` | `/healthz`, `/version` |
| `docker-compose.yml` | Base compose config |
| `docker-compose.prod.yml` | Production overrides (nginx, no exposed ports) |
| `infra/nginx/conf.d/api.conf` | Nginx HTTPS config |
| `.env` | Environment variables |

## See Also

- [MINIAPP_DEPLOY.md](./MINIAPP_DEPLOY.md) — Full deployment guide
- [MINIAPP_API_SPEC.md](./MINIAPP_API_SPEC.md) — API specification
- [MINIAPP_RUNBOOK.md](./MINIAPP_RUNBOOK.md) — Step-by-step runbook
