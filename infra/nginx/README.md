# Nginx HTTPS Reverse Proxy

This directory contains Nginx configuration for HTTPS termination on VPS.

## Architecture

```
Internet (HTTPS)
       │
       ▼
┌─────────────────┐
│     Nginx       │  :443 (HTTPS) / :80 (redirect)
│   (SSL term)    │
└────────┬────────┘
         │ proxy_pass http://api:8000
         ▼
┌─────────────────┐
│   API Service   │  :8000 (internal HTTP)
│   (FastAPI)     │
└─────────────────┘
```

## Quick Start

### 1. Replace Domain Placeholders

Edit `nginx.conf` and replace all `<DOMAIN>` with your actual domain:

```bash
# Example: replace <DOMAIN> with vibemom.ru
sed -i 's/<DOMAIN>/vibemom.ru/g' infra/nginx/nginx.conf
```

### 2. Configure DNS

Add A record pointing to your VPS IP:

| Type | Name | Value |
|------|------|-------|
| A | api | 89.191.226.233 |

Wait for DNS propagation (can take up to 24h, usually 5-15 min).

### 3. Start Nginx (HTTP only first)

For initial certificate generation, temporarily use HTTP-only config:

```bash
# Comment out SSL server block in nginx.conf first, or use init config
docker compose up -d nginx
```

### 4. Generate SSL Certificates

```bash
# Run certbot to get certificates
docker compose run --rm certbot certonly \
  --webroot \
  -w /var/www/certbot \
  -d api.<DOMAIN> \
  --email your-email@example.com \
  --agree-tos \
  --non-interactive

# Check certificates were created
ls -la infra/certbot/conf/live/api.<DOMAIN>/
```

### 5. Enable HTTPS and Restart

```bash
# Uncomment SSL server block in nginx.conf
docker compose restart nginx

# Verify HTTPS works
curl -I https://api.<DOMAIN>/healthz
```

## Files

| File | Purpose |
|------|---------|
| `conf.d/api.conf` | Main Nginx configuration with HTTPS (loaded by nginx) |
| `conf.d/api-http-only.conf.bak` | HTTP-only config for initial cert setup (NOT loaded — `.bak` extension) |
| `nginx.conf` | Standalone config (reference only, not mounted in prod) |
| `../certbot/www/` | ACME challenge directory |
| `../certbot/conf/` | Let's Encrypt certificates |

> **IMPORTANT:** Only ONE `.conf` file should exist in `conf.d/` at a time.
> Nginx loads ALL `*.conf` files, and duplicates cause startup failure.

## Certificate Renewal

Let's Encrypt certificates expire after 90 days. Set up auto-renewal:

### Option A: Cron Job (Recommended)

```bash
# Add to crontab -e
0 0 1 * * cd /root/vibemom && docker compose run --rm certbot renew && docker compose restart nginx
```

### Option B: Manual Renewal

```bash
docker compose run --rm certbot renew
docker compose restart nginx
```

## Troubleshooting

### Certificate Not Found

1. Ensure DNS is configured correctly:
   ```bash
   dig api.<DOMAIN>
   ```

2. Check ACME challenge is accessible:
   ```bash
   curl http://api.<DOMAIN>/.well-known/acme-challenge/test
   ```

3. View certbot logs:
   ```bash
   docker compose logs certbot
   ```

### 502 Bad Gateway

1. Check API container is running:
   ```bash
   docker compose ps api
   ```

2. Check API health inside nginx network:
   ```bash
   docker compose exec nginx wget -qO- http://api:8000/healthz
   ```

### SSL Handshake Errors

1. Verify certificate paths:
   ```bash
   docker compose exec nginx ls -la /etc/letsencrypt/live/api.<DOMAIN>/
   ```

2. Test SSL configuration:
   ```bash
   curl -vvv https://api.<DOMAIN>/healthz
   ```

## Security Notes

- Certificates are stored in `infra/certbot/conf/` (gitignored)
- Never commit certificates or private keys
- Use strong SSL configuration (TLS 1.2+, modern ciphers)
- Rate limiting protects against abuse (30 req/s, burst 50)

## Environment Variables

These should be set in `.env` on VPS:

```env
# Your domain (used in documentation only)
API_DOMAIN=api.<DOMAIN>

# Public URL (used by API for CORS and diagnostics)
API_PUBLIC_URL=https://api.<DOMAIN>

# CORS origins (Vercel frontend + Telegram)
API_CORS_ORIGINS=https://<vercel-app>.vercel.app,https://web.telegram.org
```
