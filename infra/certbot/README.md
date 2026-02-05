# Certbot SSL Certificate Management

Let's Encrypt SSL certificates for API HTTPS termination.

## Placeholders

Replace before use:
- `<API_DOMAIN>` = `api.example.com` (your API subdomain)
- `<EMAIL>` = `admin@example.com` (for Let's Encrypt notifications)

## Prerequisites

1. **DNS configured**: A record `<API_DOMAIN>` → VPS IP
2. **Ports open**: 80 and 443 on VPS firewall
3. **Nginx running**: HTTP server for ACME challenge

## Initial Certificate Issue

### Step 1: Start nginx (HTTP-only mode for ACME)

Before first certificate, nginx needs to serve ACME challenge on port 80:

```bash
# Start nginx (will fail on HTTPS but serve HTTP)
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d nginx || true
```

### Step 2: Issue certificate

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml run --rm certbot \
  certonly \
  --webroot \
  -w /var/www/certbot \
  -d <API_DOMAIN> \
  --email <EMAIL> \
  --agree-tos \
  --non-interactive
```

### Step 3: Restart nginx with SSL

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml restart nginx
```

### Step 4: Verify

```bash
curl -I https://<API_DOMAIN>/healthz
# Expected: HTTP/2 200
```

## Certificate Renewal

Let's Encrypt certificates expire every 90 days.

### Manual Renewal

```bash
# Renew certificates
docker compose -f docker-compose.yml -f docker-compose.prod.yml run --rm certbot renew

# Reload nginx to pick up new certs
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec nginx nginx -s reload
```

### Automatic Renewal (Cron)

Add to crontab (`crontab -e` on VPS):

```cron
# Renew SSL certificates on 1st and 15th of each month at 3:00 AM
0 3 1,15 * * cd /root/vibemom && docker compose -f docker-compose.yml -f docker-compose.prod.yml run --rm certbot renew --quiet && docker compose -f docker-compose.yml -f docker-compose.prod.yml exec nginx nginx -s reload
```

## Troubleshooting

### "Connection refused" during ACME challenge

1. Check nginx is running: `docker compose ps nginx`
2. Check port 80 is open: `curl http://<API_DOMAIN>/.well-known/acme-challenge/test`
3. Check firewall: `ufw status` or `iptables -L`

### "DNS problem: NXDOMAIN"

1. Verify DNS: `dig <API_DOMAIN>`
2. Wait for DNS propagation (up to 24h, usually 5-15 min)

### Certificate not found after issue

1. Check certificate exists:
   ```bash
   docker compose -f docker-compose.yml -f docker-compose.prod.yml run --rm certbot certificates
   ```

2. Check volume contents:
   ```bash
   docker volume inspect vibemom_letsencrypt
   ```

### Nginx fails to start with SSL

1. Check certificate paths match nginx config
2. Verify certificate was issued for correct domain
3. Check nginx config syntax: `docker compose exec nginx nginx -t`

## Certificate Paths

Certificates are stored in Docker volume `letsencrypt` and mounted to nginx:

| Path | Description |
|------|-------------|
| `/etc/letsencrypt/live/<API_DOMAIN>/fullchain.pem` | Certificate chain |
| `/etc/letsencrypt/live/<API_DOMAIN>/privkey.pem` | Private key |

## Security Notes

- Never commit certificates or private keys
- Use separate email for Let's Encrypt notifications
- Monitor certificate expiration (Let's Encrypt sends emails 20/10/1 days before expiry)
- Rate limits: 50 certificates per domain per week

## Quick Commands Reference

```bash
# Issue certificate (first time)
make cert-issue

# Renew certificates
make cert-renew

# Check certificate status
docker compose -f docker-compose.yml -f docker-compose.prod.yml run --rm certbot certificates

# Test nginx config
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec nginx nginx -t

# Reload nginx
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec nginx nginx -s reload
```
