# Mini App Deployment Guide

Production-ready deployment guide for Telegram Mini App: WebApp frontend on Vercel (HTTPS) + API on VPS (Docker + Nginx HTTPS).

## Architecture

```
                         Internet
                            │
           ┌────────────────┼────────────────┐
           │                │                │
           ▼                ▼                ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  Mini App UI    │  │     Nginx       │  │  Telegram Bot   │
│  (React+Vite)   │  │  (SSL Proxy)    │  │  (aiogram)      │
│                 │  │                 │  │                 │
│  Vercel         │  │  VPS :443/:80   │  │  VPS/Docker     │
│  :443 (HTTPS)   │  │                 │  │  :polling       │
└────────┬────────┘  └────────┬────────┘  └────────┬────────┘
         │                    │ proxy              │
         │                    ▼                    │
         │           ┌─────────────────┐           │
         └──────────▶│   Mini App API  │◀──────────┘
                     │   (FastAPI)     │
                     │  :8000 internal │
                     └────────┬────────┘
                              │
                              ▼
                     ┌─────────────────┐
                     │   PostgreSQL    │
                     │   :5432         │
                     └─────────────────┘
```

**Key components:**
- **Vercel**: Hosts Mini App frontend (React) with automatic HTTPS
- **Nginx**: HTTPS reverse proxy on VPS, terminates SSL, proxies to API
- **API**: FastAPI service (internal port 8000, not exposed to internet)
- **Bot**: Telegram bot with polling
- **PostgreSQL**: Shared database

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

### 3.1 DNS Configuration

Add A record pointing API subdomain to VPS IP:

| Type | Name | Value | TTL |
|------|------|-------|-----|
| A | api | `<VPS_IP>` | 300 |

Example: `api.vibemom.com` → `89.191.226.233`

Verify DNS propagation:
```bash
dig api.<API_DOMAIN>
# Should show your VPS IP
```

### 3.2 Update `.env` on VPS

```bash
# Mini App Frontend URL (from Vercel)
WEBAPP_URL=<WEBAPP_URL>

# Public API URL (your domain with SSL)
API_PUBLIC_URL=https://<API_DOMAIN>

# CORS origins (auto-includes WEBAPP_URL + localhost)
# Add Telegram origins for production
ALLOWED_ORIGINS=<WEBAPP_URL>,https://web.telegram.org,https://t.me

# JWT secret (generate secure random string!)
API_JWT_SECRET=your-very-long-secure-random-string-here

# Telegram initData verification (false in production!)
TG_INIT_DATA_SKIP_VERIFY=false
```

### 3.3 Open Firewall Ports

```bash
# If using ufw
ufw allow 80/tcp
ufw allow 443/tcp
ufw reload

# If using firewalld
firewall-cmd --permanent --add-port=80/tcp
firewall-cmd --permanent --add-port=443/tcp
firewall-cmd --reload
```

### 3.4 Deploy on VPS (Production)

```bash
# Pull latest code
cd /root/vibemom
git pull origin v2-editor

# Production deployment with nginx
make up-prod

# Or manually:
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build db bot api nginx

# Check status
make ps-prod

# Check logs
make logs-prod
```

## Step 4: SSL Certificate Setup

### 4.1 Issue Certificate (First Time)

```bash
# Using Makefile (recommended)
make cert-issue DOMAIN=<API_DOMAIN> EMAIL=<EMAIL>

# Or manually:
# Start nginx for ACME challenge
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d nginx || true

# Issue certificate
docker compose -f docker-compose.yml -f docker-compose.prod.yml run --rm certbot certonly \
  --webroot \
  -w /var/www/certbot \
  -d <API_DOMAIN> \
  --email <EMAIL> \
  --agree-tos \
  --non-interactive

# Restart nginx with SSL
docker compose -f docker-compose.yml -f docker-compose.prod.yml restart nginx
```

### 4.2 Certificate Renewal

```bash
# Manual renewal
make cert-renew

# Add cron job for auto-renewal (1st of each month)
crontab -e
# Add: 0 0 1 * * cd /root/vibemom && make cert-renew
```

## Step 5: Verification

### 5.1 Check API Health

```bash
# HTTPS health check (production)
curl -sS https://<API_DOMAIN>/healthz
# Expected: {"status":"ok","database":"ok"}

# Version check (includes WEBAPP_URL and API_PUBLIC_URL)
curl -sS https://<API_DOMAIN>/version
# Expected: {"version":"1.0.0","git_sha":"...","webapp_url":"https://...","api_public_url":"https://..."}

# Internal health check (from VPS)
curl http://localhost:8000/healthz
```

### 5.2 Check Bot /version Command

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

### 5.3 Check Mini App in Telegram

1. Open chat with your bot
2. Tap the **📱 Кабинет** menu button (bottom left)
3. Mini App should open and show project list

### 5.4 Check Environment Variables in Container

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

## Step 6: Configure Nginx Domain

Edit `infra/nginx/conf.d/api.conf` and replace `<API_DOMAIN>` with your domain:

```bash
# On VPS
cd /root/vibemom
sed -i 's/<API_DOMAIN>/api.vibemom.com/g' infra/nginx/conf.d/api.conf
```

Or edit manually - replace all occurrences of `<API_DOMAIN>`.

## Step 7: Full Production Stack

```bash
# On VPS
cd /root/vibemom

# Full production deployment
make up-prod

# Check all services running
make ps-prod

# Check logs
make logs-prod
```

## Environment Variables Reference

### Placeholders

| Placeholder | Example | Description |
|-------------|---------|-------------|
| `<API_DOMAIN>` | `api.example.com` | Your API subdomain (A record → VPS IP) |
| `<WEBAPP_URL>` | `https://myapp.vercel.app` | Vercel deployment URL |
| `<EMAIL>` | `admin@example.com` | Email for Let's Encrypt |

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
| `ALLOWED_ORIGINS` | CORS origins (comma-separated, preferred) | Recommended |
| `WEBAPP_ORIGINS` | Legacy CORS origins (comma-separated) | Optional |
| `API_CORS_ORIGINS` | Legacy CORS config | Optional |
| `API_JWT_SECRET` | JWT signing secret (min 32 chars) | Yes |
| `TG_INIT_DATA_SKIP_VERIFY` | Skip initData validation (debug only!) | No (default: false) |

### Frontend (Vercel Environment Variables)

| Variable | Description | Required |
|----------|-------------|----------|
| `VITE_API_PUBLIC_URL` | Public API URL (e.g., `https://<API_DOMAIN>`) | Yes |

## Quick Commands Reference

```bash
# =============================================================================
# Production (with nginx + SSL)
# =============================================================================

# Start production stack
make up-prod

# Check status
make ps-prod

# View logs
make logs-prod        # All services
make logs-nginx       # Nginx only (60 lines)
make logs-api         # API only (80 lines)
make logs-bot         # Bot only (80 lines)

# =============================================================================
# SSL Certificates
# =============================================================================

# Issue certificate (first time)
make cert-issue DOMAIN=<API_DOMAIN> EMAIL=<EMAIL>

# Renew certificates
make cert-renew

# Check certificate status
make cert-status

# =============================================================================
# Health Checks
# =============================================================================

# HTTPS health check (production)
curl -sS https://<API_DOMAIN>/healthz
curl -sS https://<API_DOMAIN>/version

# Internal health check (from VPS)
curl http://localhost:8000/healthz

# Check env in container
docker compose exec api printenv | grep -E "(WEBAPP|CORS|ALLOWED)"

# =============================================================================
# Nginx
# =============================================================================

# Test nginx config syntax
make nginx-test

# Reload nginx (without restart)
make nginx-reload

# =============================================================================
# Development (local)
# =============================================================================

# Start dev stack (without nginx)
make up

# Run frontend locally
cd services/webapp && npm run dev
```
