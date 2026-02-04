#!/bin/sh
set -e

APP_ENV="${APP_ENV:-local}"
AUTO_MIGRATE="${AUTO_MIGRATE:-true}"

if [ "$APP_ENV" = "production" ]; then
  echo "APP_ENV=production: skipping auto-migrations"
else
  if [ "$AUTO_MIGRATE" = "true" ]; then
    echo "AUTO_MIGRATE=true: running alembic upgrade head"
    alembic upgrade head
  else
    echo "AUTO_MIGRATE=false: skipping auto-migrations"
  fi
fi

exec python main.py
