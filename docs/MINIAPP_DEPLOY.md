# Mini App Deployment Guide

Production-ready deployment guide for Telegram Mini App: WebApp frontend on Vercel (HTTPS) + API on VPS (Docker).

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Telegram Bot   │     │   Mini App API  │     │  Mini App UI    │
│  (aiogram)      │     │   (FastAPI)     │     │  (React+Vite)   │
│                 │     │                 │     │                 │
│  VPS/Docker     │     │  VPS/Docker     │     │  Vercel         │
│  :polling       │────▶│  :8000          │◀────│  :443 (HTTPS)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                         PostgreSQL                               │
└─────────────────────────────────────────────────────────────────┘
```

## Step 1: Deploy Frontend to Vercel

### 1.1 Via Vercel Dashboard (Recommended)

1. Go to [vercel.com](https://vercel.com) and sign in
2. Click **"Add New... → Project"**
3. **Import** your GitHub repository
4. Configure:
   - **Root Directory**: `services/webapp`
   - **Framework Preset**: Vite (auto-detected)
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
5. **Environment Variables** (Settings → Environment Variables):

| Variable | Value | Environment |
|----------|-------|-------------|
| `VITE_API_PUBLIC_URL` | `https://api.yourdomain.com` | Production |

6. Click **Deploy**
7. Note the URL: `https://your-app.vercel.app`

### 1.2 Via Vercel CLI (Alternative)

```bash
# Install Vercel CLI
npm install -g vercel

# Navigate to webapp directory
cd services/webapp

# Deploy (follow prompts)
vercel

# Production deploy
vercel --prod
```

## Step 2: Configure BotFather

### 2.1 Set Menu Button (WebApp)

1. Open @BotFather in Telegram
2. Send `/mybots`
3. Select your bot
4. **Bot Settings → Menu Button → Configure menu button**
5. Enter URL: `https://your-app.vercel.app`
6. Enter text: `📱 Кабинет`

### 2.2 Set Web App Domain

1. In BotFather: **Bot Settings → Domain → Set Domain**
2. Enter domain without protocol: `your-app.vercel.app`

> **Important**: Domain must be HTTPS!

## Step 3: Configure VPS Environment

### 3.1 Update `.env` on VPS

```bash
# Mini App Frontend URL (from Vercel)
WEBAPP_URL=https://your-app.vercel.app

# Public API URL (your domain with SSL, or IP:port for debug)
API_PUBLIC_URL=https://api.yourdomain.com

# CORS origins (auto-includes WEBAPP_URL + localhost)
# Add extra origins if needed:
WEBAPP_ORIGINS=https://web.telegram.org

# JWT secret (generate secure random string!)
API_JWT_SECRET=your-very-long-secure-random-string-here

# Telegram initData verification (false in production!)
TG_INIT_DATA_SKIP_VERIFY=false
```

### 3.2 Deploy on VPS

```bash
# Pull latest code
cd /root/vibemom  # or your project directory
git pull origin v2-editor

# Rebuild and restart
docker compose up -d --build api bot

# Check status
docker compose ps

# Check logs
docker compose logs -f bot api
```

## Step 4: Verification

### 4.1 Check API Health

```bash
# Health check (on VPS)
curl http://localhost:8000/healthz
# Expected: {"status":"ok","database":"ok"}

# Version check (includes WEBAPP_URL and API_PUBLIC_URL)
curl http://localhost:8000/version
# Expected: {"version":"1.0.0","git_sha":"...","webapp_url":"https://...","api_public_url":"https://..."}
```

### 4.2 Check Bot /version Command

In Telegram chat with your bot:
```
/version
```

Expected response:
```
🔧 Version Info

SHA: abc1234
Branch: v2-editor
Build: 2024-01-15T12:00:00Z
Env: production
V2: true

WebApp URL: https://your-app.vercel.app
API URL: https://api.yourdomain.com
```

### 4.3 Check Mini App in Telegram

1. Open chat with your bot
2. Tap the **📱 Кабинет** menu button (bottom left)
3. Mini App should open and show project list

### 4.4 Check Environment Variables in Container

```bash
docker compose exec api printenv | grep -E "(WEBAPP_URL|API_PUBLIC_URL)"
docker compose exec bot printenv | grep -E "(WEBAPP_URL|API_PUBLIC_URL)"
```

## Debug Mode (Without SSL)

> ⚠️ **Warning**: Debug mode works only in browser, NOT in Telegram WebApp (requires HTTPS).

### For Local Browser Testing

1. Set Vercel env:
   ```
   VITE_API_PUBLIC_URL=http://<VPS_IP>:8000
   ```

2. Set VPS env:
   ```env
   TG_INIT_DATA_SKIP_VERIFY=true
   WEBAPP_URL=http://localhost:5173
   ```

3. Run frontend locally:
   ```bash
   cd services/webapp
   npm install
   npm run dev
   # Open http://localhost:5173
   ```

### Limitations

- Telegram WebApp requires HTTPS — cannot test full flow without SSL
- `TG_INIT_DATA_SKIP_VERIFY=true` is insecure — anyone can impersonate users
- Use only for initial development/debugging

## Troubleshooting

### Mini App Not Opening

1. Check `WEBAPP_URL` starts with `https://`
2. Verify domain is set in BotFather
3. Check bot logs: `docker compose logs bot`

### "VITE_API_PUBLIC_URL is not set" Error

1. Go to Vercel → Project Settings → Environment Variables
2. Add `VITE_API_PUBLIC_URL` with your API URL
3. Redeploy: **Deployments → ... → Redeploy**

### CORS Errors

1. Check `WEBAPP_ORIGINS` includes your Vercel URL
2. Or: `WEBAPP_URL` is set (auto-added to CORS)
3. Rebuild API: `docker compose up -d --build api`
4. Check allowed origins in logs:
   ```bash
   docker compose logs api | grep "CORS enabled"
   ```

### "Invalid hash signature" Error

1. Verify `BOT_TOKEN` is correct in API `.env`
2. For testing: set `TG_INIT_DATA_SKIP_VERIFY=true` (insecure!)
3. **Never use skip verify in production!**

### API Not Reachable from Vercel

1. Check API is accessible: `curl http://<VPS_IP>:8000/healthz`
2. Check firewall allows port 8000
3. For production: set up Nginx/Caddy with SSL (see next section)

## Next Steps: Production SSL

For production, set up reverse proxy with SSL termination:

1. **Option A: Caddy** (automatic HTTPS)
2. **Option B: Nginx + Let's Encrypt**

This is covered in a separate guide. The current setup works for:
- Development and debugging
- Browser testing (without Telegram WebApp features)
- Verifying all components work together

## Environment Variables Reference

### Bot (`.env` on VPS)

| Variable | Description | Required |
|----------|-------------|----------|
| `WEBAPP_URL` | HTTPS URL of Vercel frontend | Yes |
| `API_PUBLIC_URL` | Public API URL | Yes (for diagnostics) |
| `BOT_TOKEN` | Telegram Bot Token | Yes |

### API (`.env` on VPS)

| Variable | Description | Required |
|----------|-------------|----------|
| `BOT_TOKEN` | Telegram Bot Token (for initData validation) | Yes |
| `WEBAPP_URL` | WebApp URL (auto-added to CORS) | Recommended |
| `API_PUBLIC_URL` | Public API URL (for diagnostics) | Recommended |
| `WEBAPP_ORIGINS` | Extra CORS origins (comma-separated) | Optional |
| `API_JWT_SECRET` | JWT signing secret (min 32 chars) | Yes |
| `TG_INIT_DATA_SKIP_VERIFY` | Skip initData validation (debug only!) | No (default: false) |

### Frontend (Vercel Environment Variables)

| Variable | Description | Required |
|----------|-------------|----------|
| `VITE_API_PUBLIC_URL` | Public API URL | Yes |

## Quick Commands Reference

```bash
# VPS: rebuild and restart
docker compose up -d --build api bot

# VPS: check logs
docker compose logs -f bot api

# VPS: check health
curl http://localhost:8000/healthz

# VPS: check version
curl http://localhost:8000/version

# VPS: check env in container
docker compose exec api printenv | grep WEBAPP

# Local: run frontend
cd services/webapp && npm run dev
```
