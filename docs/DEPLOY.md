# Деплой на VPS (v2-editor)

Автодеплой при push в ветку `v2-editor`: GitHub Actions подключается по SSH к VPS, обновляет код в `/root/vibemom`, пересобирает и перезапускает контейнеры.

Репозиторий: `git@github.com:GoodLifeFM/vibemom.git`. На VPS проект лежит в `/root/vibemom`.

## GitHub Secrets

В репозитории: **Settings → Secrets and variables → Actions** добавьте:

| Secret        | Обязательный | Описание |
|---------------|--------------|----------|
| `VPS_HOST`    | да           | IP или hostname VPS (например `89.191.226.233`) |
| `VPS_USER`    | да           | SSH-пользователь (например `root`) |
| `VPS_SSH_KEY` | да           | Приватный SSH-ключ целиком (включая `-----BEGIN ... KEY-----` и `-----END ... KEY-----`) |
| `VPS_PORT`    | нет          | Порт SSH; если не задан — 22 |
| `VPS_KNOWN_HOSTS` | нет     | Опционально: строка для `~/.ssh/known_hosts` (результат `ssh-keyscan -p PORT HOST`). По умолчанию workflow использует `StrictHostKeyChecking=no`. |

## Приватный ключ и доступ по SSH

1. **Сгенерировать ключ** (на своей машине):

   ```bash
   ssh-keygen -t ed25519 -C "github-actions-vibemom" -f ~/.ssh/vibemom_deploy -N ""
   ```

2. **Добавить ключ в GitHub:**  
   Содержимое файла `~/.ssh/vibemom_deploy` (приватный ключ) скопировать в секрет `VPS_SSH_KEY`.

3. **Добавить публичный ключ на VPS** (под пользователем `VPS_USER`):

   ```bash
   mkdir -p ~/.ssh
   chmod 700 ~/.ssh
   echo "СОДЕРЖИМОЕ_ФАЙЛА_vibemom_deploy.pub" >> ~/.ssh/authorized_keys
   chmod 600 ~/.ssh/authorized_keys
   ```

   Или: на локальной машине выполнить `cat ~/.ssh/vibemom_deploy.pub` и вставить одну строку в `~/.ssh/authorized_keys` на VPS.

## Проверка

1. Сделайте **push в ветку `v2-editor`** (или merge PR в `v2-editor`).
2. Откройте **Actions** в репозитории → workflow **Deploy to VPS (v2-editor)**.
3. В логах job должны быть: проверка docker/docker compose, `git pull`, `docker compose up -d --build`, `docker compose ps`, последние 80 строк логов сервиса `bot`.

Если на VPS нет `docker` или `docker compose`, workflow завершится с ошибкой и выведет сообщение: *docker not found* или *docker compose not found* — установите их на VPS и повторите деплой.

## Откат

На VPS в каталоге проекта:

```bash
cd /root/vibemom
git fetch --all
git reset --hard <hash_коммита>
docker compose up -d --build
```

Замените `<hash_коммита>` на нужный коммит (например из `git log`).
