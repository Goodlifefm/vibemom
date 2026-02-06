#!/bin/bash
# =============================================================================
# VPS Deployment Script for Vibemom Mini App
# =============================================================================
#
# This script sets up the complete production environment:
# - Docker containers (db, bot, api, nginx)
# - SSL certificates via Let's Encrypt
# - Environment configuration
#
# Prerequisites:
# - Docker and Docker Compose installed
# - DNS A record: api.vibemom.ru -> 89.191.226.233
# - Port 80 and 443 open in firewall
#
# Usage:
#   ./scripts/deploy-vps.sh
#
# =============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
API_DOMAIN="api.vibemom.ru"
WEBAPP_URL="${WEBAPP_URL:-https://vibemom.ru}"  # Override with env if needed
PROJECT_DIR="/root/vibemom"
EMAIL="${CERT_EMAIL:-admin@vibemom.ru}"

echo -e "${GREEN}=== Vibemom VPS Deployment ===${NC}"
echo "API Domain: $API_DOMAIN"
echo "WebApp URL: $WEBAPP_URL"
echo "Project Dir: $PROJECT_DIR"
echo ""

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}Error: docker-compose.yml not found. Are you in the project root?${NC}"
    exit 1
fi

# =============================================================================
# Step 1: Ensure .env exists
# =============================================================================
echo -e "${YELLOW}Step 1: Checking .env file...${NC}"

if [ ! -f ".env" ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo -e "${RED}IMPORTANT: Edit .env and set BOT_TOKEN before continuing!${NC}"
    echo "Run: nano .env"
    exit 1
fi

# Ensure required environment variables
if ! grep -q "^WEBAPP_URL=" .env || grep -q "^WEBAPP_URL=$" .env; then
    echo "Setting WEBAPP_URL in .env..."
    sed -i "s|^WEBAPP_URL=.*|WEBAPP_URL=$WEBAPP_URL|" .env 2>/dev/null || \
        echo "WEBAPP_URL=$WEBAPP_URL" >> .env
fi

if ! grep -q "^API_PUBLIC_URL=" .env || grep -q "^API_PUBLIC_URL=$" .env; then
    echo "Setting API_PUBLIC_URL in .env..."
    sed -i "s|^API_PUBLIC_URL=.*|API_PUBLIC_URL=https://$API_DOMAIN|" .env 2>/dev/null || \
        echo "API_PUBLIC_URL=https://$API_DOMAIN" >> .env
fi

if ! grep -q "^ALLOWED_ORIGINS=" .env || grep -q "^ALLOWED_ORIGINS=$" .env; then
    echo "Setting ALLOWED_ORIGINS in .env..."
    ORIGINS="$WEBAPP_URL,https://web.telegram.org,https://t.me"
    sed -i "s|^ALLOWED_ORIGINS=.*|ALLOWED_ORIGINS=$ORIGINS|" .env 2>/dev/null || \
        echo "ALLOWED_ORIGINS=$ORIGINS" >> .env
fi

echo -e "${GREEN}✓ .env configured${NC}"
echo ""

# =============================================================================
# Step 2: Check DNS
# =============================================================================
echo -e "${YELLOW}Step 2: Checking DNS for $API_DOMAIN...${NC}"

DNS_IP=$(dig +short $API_DOMAIN 2>/dev/null || echo "")
if [ -z "$DNS_IP" ]; then
    echo -e "${RED}Warning: DNS not resolving for $API_DOMAIN${NC}"
    echo "Please add A record: $API_DOMAIN -> YOUR_VPS_IP"
    echo "Continuing anyway (you may need to fix DNS later)..."
else
    echo -e "${GREEN}✓ DNS resolves to: $DNS_IP${NC}"
fi
echo ""

# =============================================================================
# Step 3: Start services (HTTP only for cert)
# =============================================================================
echo -e "${YELLOW}Step 3: Starting services with HTTP-only nginx...${NC}"

# Use HTTP-only config for initial setup
if [ -f "infra/nginx/conf.d/api.conf" ] && [ -f "infra/nginx/conf.d/api-http-only.conf" ]; then
    # Check if SSL certs exist
    if ! docker volume inspect vibemom_letsencrypt >/dev/null 2>&1 || \
       ! docker run --rm -v vibemom_letsencrypt:/etc/letsencrypt alpine ls /etc/letsencrypt/live/$API_DOMAIN 2>/dev/null | grep -q .; then
        echo "No SSL certificates found. Using HTTP-only config..."
        mv infra/nginx/conf.d/api.conf infra/nginx/conf.d/api.conf.ssl
        cp infra/nginx/conf.d/api-http-only.conf infra/nginx/conf.d/api.conf
        HTTP_ONLY=true
    else
        echo "SSL certificates found. Using HTTPS config..."
        HTTP_ONLY=false
    fi
else
    HTTP_ONLY=false
fi

# Build and start
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build db bot api nginx

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 10

# Check API health
echo "Checking API health..."
if curl -sS --max-time 5 http://localhost:8000/healthz | grep -q "ok"; then
    echo -e "${GREEN}✓ API is healthy${NC}"
else
    echo -e "${YELLOW}Warning: API health check failed (may still be starting)${NC}"
fi

echo ""

# =============================================================================
# Step 4: Issue SSL certificate (if needed)
# =============================================================================
if [ "${HTTP_ONLY:-false}" = "true" ]; then
    echo -e "${YELLOW}Step 4: Issuing SSL certificate...${NC}"
    
    # Check if nginx is responding on HTTP
    if curl -sS --max-time 5 "http://$API_DOMAIN/healthz" 2>/dev/null | grep -q "ok"; then
        echo "HTTP endpoint is accessible. Issuing certificate..."
        
        docker compose -f docker-compose.yml -f docker-compose.prod.yml run --rm certbot certonly \
            --webroot \
            -w /var/www/certbot \
            -d $API_DOMAIN \
            --email $EMAIL \
            --agree-tos \
            --non-interactive
        
        # Restore HTTPS config
        echo "Restoring HTTPS config..."
        mv infra/nginx/conf.d/api.conf.ssl infra/nginx/conf.d/api.conf
        
        # Restart nginx with SSL
        docker compose -f docker-compose.yml -f docker-compose.prod.yml restart nginx
        
        echo -e "${GREEN}✓ SSL certificate issued${NC}"
    else
        echo -e "${RED}Warning: HTTP endpoint not accessible. Cannot issue certificate.${NC}"
        echo "Please ensure:"
        echo "  1. DNS is properly configured"
        echo "  2. Port 80 is open in firewall"
        echo "  3. Nginx is running"
        echo ""
        echo "After fixing, run: make cert-issue DOMAIN=$API_DOMAIN EMAIL=$EMAIL"
    fi
else
    echo -e "${YELLOW}Step 4: SSL certificates already exist, skipping...${NC}"
fi

echo ""

# =============================================================================
# Step 5: Verify deployment
# =============================================================================
echo -e "${YELLOW}Step 5: Verifying deployment...${NC}"

echo "Container status:"
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps

echo ""
echo "API endpoints:"

# Internal check
echo -n "  Internal (localhost:8000/healthz): "
if curl -sS --max-time 5 http://localhost:8000/healthz 2>/dev/null | grep -q "ok"; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FAIL${NC}"
fi

# HTTP check
echo -n "  HTTP ($API_DOMAIN/healthz): "
if curl -sS --max-time 5 "http://$API_DOMAIN/healthz" 2>/dev/null | grep -q "ok"; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${YELLOW}N/A (redirects to HTTPS)${NC}"
fi

# HTTPS check
echo -n "  HTTPS ($API_DOMAIN/healthz): "
if curl -sS --max-time 5 "https://$API_DOMAIN/healthz" 2>/dev/null | grep -q "ok"; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FAIL${NC}"
fi

echo ""

# =============================================================================
# Summary
# =============================================================================
echo -e "${GREEN}=== Deployment Summary ===${NC}"
echo ""
echo "API URL: https://$API_DOMAIN"
echo "WebApp URL: $WEBAPP_URL"
echo ""
echo "Test commands:"
echo "  curl https://$API_DOMAIN/healthz"
echo "  curl https://$API_DOMAIN/version"
echo ""
echo "Logs:"
echo "  make logs-prod"
echo "  make logs-api"
echo "  make logs-nginx"
echo ""
echo -e "${GREEN}Done!${NC}"
