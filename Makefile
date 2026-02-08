# =============================================================================
# Makefile for Vibe Market
# =============================================================================
#
# Usage:
#   make help          - Show available commands
#   make up-prod       - Start production stack
#   make logs-api      - Show API logs
#
# =============================================================================

.PHONY: help up up-prod down logs logs-api logs-bot logs-nginx \
        cert-issue cert-renew build test lint

# Default target
help:
	@echo "Vibe Market - Available commands:"
	@echo ""
	@echo "Development:"
	@echo "  make up              Start dev stack (db + bot + api)"
	@echo "  make down            Stop all containers"
	@echo "  make build           Build images without cache"
	@echo "  make logs            Follow all logs"
	@echo ""
	@echo "Production:"
	@echo "  make up-prod         Start production stack (with nginx + SSL)"
	@echo "  make down-prod       Stop production stack"
	@echo "  make logs-nginx      Show nginx logs (60 lines)"
	@echo "  make logs-api        Show API logs (80 lines)"
	@echo "  make logs-bot        Show bot logs (80 lines)"
	@echo ""
	@echo "SSL Certificates:"
	@echo "  make cert-issue      Issue SSL certificate (first time)"
	@echo "  make cert-renew      Renew SSL certificates"
	@echo "  make cert-status     Check certificate status"
	@echo ""
	@echo "Testing:"
	@echo "  make test            Run tests"
	@echo "  make lint            Run linter"
	@echo "  make health          Check API health"
	@echo ""

# =============================================================================
# Development
# =============================================================================

DEV_COMPOSE = docker compose -f docker-compose.yml -f docker-compose.dev.yml

up:
	$(DEV_COMPOSE) up -d --build db bot api

down:
	$(DEV_COMPOSE) down

build:
	$(DEV_COMPOSE) build --no-cache bot api

logs:
	$(DEV_COMPOSE) logs -f

# =============================================================================
# Production
# =============================================================================

PROD_COMPOSE = docker compose -f docker-compose.yml -f docker-compose.prod.yml

up-prod:
	$(PROD_COMPOSE) up -d --build db bot api nginx

down-prod:
	$(PROD_COMPOSE) down

restart-prod:
	$(PROD_COMPOSE) restart db bot api nginx

logs-nginx:
	$(PROD_COMPOSE) logs --tail=60 nginx

logs-api:
	$(PROD_COMPOSE) logs --tail=80 api

logs-bot:
	$(PROD_COMPOSE) logs --tail=80 bot

logs-prod:
	$(PROD_COMPOSE) logs -f bot api nginx

# =============================================================================
# SSL Certificates
# =============================================================================

# Issue certificate (first time)
# Usage: make cert-issue DOMAIN=api.example.com EMAIL=admin@example.com
cert-issue:
ifndef DOMAIN
	$(error DOMAIN is required. Usage: make cert-issue DOMAIN=api.example.com EMAIL=admin@example.com)
endif
ifndef EMAIL
	$(error EMAIL is required. Usage: make cert-issue DOMAIN=api.example.com EMAIL=admin@example.com)
endif
	@echo "Starting nginx for ACME challenge..."
	$(PROD_COMPOSE) up -d nginx || true
	@sleep 3
	@echo "Issuing certificate for $(DOMAIN)..."
	$(PROD_COMPOSE) run --rm certbot certonly \
		--webroot \
		-w /var/www/certbot \
		-d $(DOMAIN) \
		--email $(EMAIL) \
		--agree-tos \
		--non-interactive
	@echo "Restarting nginx with SSL..."
	$(PROD_COMPOSE) restart nginx
	@echo "Done! Test with: curl -I https://$(DOMAIN)/healthz"

# Renew certificates
cert-renew:
	$(PROD_COMPOSE) run --rm certbot renew
	$(PROD_COMPOSE) exec nginx nginx -s reload

# Check certificate status
cert-status:
	$(PROD_COMPOSE) run --rm certbot certificates

# =============================================================================
# Testing & Health
# =============================================================================

test:
	python -m pytest tests/ -v

lint:
	ruff check .

health:
	@echo "Checking API health..."
	@curl -sS http://localhost:8000/healthz || echo "API not responding on localhost:8000"

health-prod:
	@echo "Checking production API health..."
	@echo "Usage: make health-prod DOMAIN=api.example.com"
ifdef DOMAIN
	@curl -sS https://$(DOMAIN)/healthz || echo "API not responding"
	@curl -sS https://$(DOMAIN)/version || echo "Version endpoint not responding"
else
	@echo "DOMAIN not set. Trying localhost..."
	@curl -sS http://localhost:8000/healthz || echo "API not responding"
endif

# =============================================================================
# Utilities
# =============================================================================

# Show running containers
ps:
	$(DEV_COMPOSE) ps

ps-prod:
	$(PROD_COMPOSE) ps

# Shell into container
shell-api:
	$(DEV_COMPOSE) exec api sh

shell-bot:
	$(DEV_COMPOSE) exec bot bash

shell-nginx:
	$(PROD_COMPOSE) exec nginx sh

# Check nginx config syntax
nginx-test:
	$(PROD_COMPOSE) exec nginx nginx -t

# Reload nginx without restart
nginx-reload:
	$(PROD_COMPOSE) exec nginx nginx -s reload
