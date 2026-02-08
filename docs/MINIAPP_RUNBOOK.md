# Mini App — Руководство по развёртыванию

Пошаговая инструкция для запуска Mini App (WebApp на Vercel + API на VPS).

## Обзор архитектуры

```
┌─────────────────┐     HTTPS      ┌─────────────────┐
│   Telegram      │ ────────────▶  │     Vercel      │
│   WebApp        │                │  (Frontend)     │
└─────────────────┘                └────────┬────────┘
                                            │
                                            │ HTTPS
                                            ▼
                                   ┌─────────────────┐
                                   │   VPS (API)     │
                                   │  Nginx + API    │
                                   │  + Bot + DB     │
                                   └─────────────────┘
```

---

## 1. Vercel: деплой Frontend

### 1.1 Импорт проекта

1. Откройте [vercel.com](https://vercel.com) → **Add New Project**
2. Импортируйте репозиторий `vibe-market`
3. Настройте проект:
   - **Root Directory**: `services/webapp`
   - **Framework Preset**: Vite
   - **Build Command**: `npm run build` (по умолчанию)
   - **Output Directory**: `dist` (по умолчанию)

### 1.2 Environment Variables

В настройках проекта (Settings → Environment Variables) добавьте:

| Variable | Value | Scope |
|----------|-------|-------|
| `VITE_API_PUBLIC_URL` | `https://api.<YOUR_DOMAIN>` | Production, Preview |

> ⚠️ **Важно**: Переменная должна начинаться с `VITE_` для доступа из фронтенда.

### 1.3 Деплой

```bash
# Локально (опционально)
cd services/webapp
npm install
npm run build

# Через Vercel CLI
vercel --prod
```

После деплоя получите URL: `https://your-project.vercel.app`

---

## 2. DNS: настройка домена

### 2.1 A-запись для API

Добавьте DNS-запись у вашего регистратора:

| Тип | Имя | Значение | TTL |
|-----|-----|----------|-----|
| A | `api` | `<VPS_IP>` | 300 |

**Пример**: `api.vibemom.ru` → `89.191.226.233`

### 2.2 Проверка DNS

```bash
# Дождитесь распространения (5-60 минут)
nslookup api.<YOUR_DOMAIN>
# или
dig api.<YOUR_DOMAIN>
```

---

## 3. VPS: запуск сервисов

### 3.1 Подготовка

```bash
# SSH на сервер
ssh root@<VPS_IP>

# Перейти в папку проекта
cd /root/vibemom

# Обновить код
git pull origin v2-editor
```

### 3.2 Настройка .env

```bash
# Создать/обновить .env
cat > .env << 'EOF'
BOT_TOKEN=<YOUR_BOT_TOKEN>
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/vibe_market
POSTGRES_PASSWORD=postgres

# Mini App URLs
WEBAPP_URL=https://your-project.vercel.app
API_PUBLIC_URL=https://api.<YOUR_DOMAIN>

# CORS (опционально, если нужны доп. домены)
ALLOWED_ORIGINS=https://web.telegram.org,https://t.me

# JWT (поменять в продакшене!)
API_JWT_SECRET=<RANDOM_SECRET_32_CHARS>
API_JWT_TTL_MIN=43200

# Прочее
LOG_LEVEL=INFO
APP_ENV=production
V2_ENABLED=false
EOF
```

### 3.3 Запуск без SSL (первичный)

```bash
# Полный перезапуск
docker compose down -v
docker compose up -d --build db api bot

# Проверка статуса
docker compose ps
docker compose logs api --tail=50
```

---

## 4. HTTPS: настройка SSL

### Вариант A: Caddy (рекомендуется — автоматический SSL)

```bash
# Установка Caddy
apt update && apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list
apt update && apt install caddy

# Конфиг Caddy
cat > /etc/caddy/Caddyfile << 'EOF'
api.<YOUR_DOMAIN> {
    reverse_proxy localhost:8000
}
EOF

# Запуск (SSL автоматически)
systemctl enable caddy
systemctl restart caddy

# Проверка
curl -I https://api.<YOUR_DOMAIN>/healthz
```

### Вариант B: Nginx + Let's Encrypt

```bash
# Установка certbot
apt install -y certbot python3-certbot-nginx nginx

# Nginx конфиг (HTTP-only для получения сертификата)
cat > /etc/nginx/sites-available/api << 'EOF'
server {
    listen 80;
    server_name api.<YOUR_DOMAIN>;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

ln -sf /etc/nginx/sites-available/api /etc/nginx/sites-enabled/
mkdir -p /var/www/certbot
nginx -t && systemctl reload nginx

# Получение сертификата
certbot certonly --webroot -w /var/www/certbot -d api.<YOUR_DOMAIN> --email <YOUR_EMAIL> --agree-tos --non-interactive

# Обновить Nginx для HTTPS
cat > /etc/nginx/sites-available/api << 'EOF'
server {
    listen 80;
    server_name api.<YOUR_DOMAIN>;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.<YOUR_DOMAIN>;

    ssl_certificate /etc/letsencrypt/live/api.<YOUR_DOMAIN>/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.<YOUR_DOMAIN>/privkey.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

nginx -t && systemctl reload nginx

# Автопродление сертификата
echo "0 0 * * * root certbot renew --quiet" >> /etc/crontab
```

---

## 5. Telegram: настройка BotFather

### 5.1 Menu Button

1. Откройте [@BotFather](https://t.me/BotFather) в Telegram
2. `/mybots` → выберите вашего бота
3. **Bot Settings** → **Menu Button** → **Configure menu button**
4. Введите URL: `https://your-project.vercel.app`
5. Введите текст кнопки: `📱 Кабинет`

### 5.2 Web App (опционально)

Если нужна отдельная команда для открытия Mini App:

1. `/mybots` → выберите бота
2. **Bot Settings** → **Configure Mini App**
3. Задайте URL Mini App

---

## 6. Чек-лист проверок

### API Health

```bash
# Health check
curl https://api.<YOUR_DOMAIN>/healthz
# Ожидается: {"status":"ok","database":"ok"}

# Version info
curl https://api.<YOUR_DOMAIN>/version
# Ожидается: {"version":"...", "git_sha":"...", "webapp_url":"...", "api_public_url":"..."}
```

### CORS проверка

```bash
# Проверка CORS headers
curl -I -X OPTIONS https://api.<YOUR_DOMAIN>/projects/my \
  -H "Origin: https://vibemom.ru" \
  -H "Access-Control-Request-Method: GET"

# Должен содержать:
# Access-Control-Allow-Origin: https://vibemom.ru
# Access-Control-Allow-Credentials: true
```

### Frontend

1. Откройте `https://your-project.vercel.app` в браузере
2. Проверьте что:
   - Нет баннера "DEMO MODE"
   - Нет CORS ошибок в консоли
   - Загружается список проектов

### Telegram WebApp

1. Откройте бота в Telegram
2. Нажмите кнопку меню (📱 Кабинет)
3. Проверьте что:
   - Mini App открывается
   - Применяется тема Telegram
   - Работает авторизация
   - Загружаются реальные данные

---

## 7. Troubleshooting

### CORS ошибки

```
Access to fetch at 'https://api...' from origin 'https://...' has been blocked by CORS policy
```

**Решение**: Проверьте что `WEBAPP_URL` в `.env` на VPS совпадает с URL Vercel.

### 401 Unauthorized

**Решение**: Убедитесь что `BOT_TOKEN` в `.env` на VPS совпадает с токеном бота.

### SSL ошибки

```bash
# Проверка сертификата
openssl s_client -connect api.<YOUR_DOMAIN>:443 -servername api.<YOUR_DOMAIN>

# Если certbot не работает — проверьте что порт 80 открыт
ufw allow 80
ufw allow 443
```

### API не отвечает

```bash
# Проверка контейнеров
docker compose ps
docker compose logs api --tail=100

# Рестарт
docker compose restart api
```

---

## 8. Быстрый старт (TL;DR)

```bash
# 1. Vercel: задеплоить services/webapp, добавить VITE_API_PUBLIC_URL

# 2. DNS: A-запись api.domain.com → VPS_IP

# 3. VPS:
ssh root@VPS_IP
cd /root/vibemom
git pull
# Настроить .env (см. секцию 3.2)
docker compose down -v && docker compose up -d --build db api bot

# 4. SSL (Caddy):
apt install caddy
echo "api.domain.com { reverse_proxy localhost:8000 }" > /etc/caddy/Caddyfile
systemctl restart caddy

# 5. Telegram: BotFather → Menu Button → URL Vercel

# 6. Проверка:
curl https://api.domain.com/healthz
```
