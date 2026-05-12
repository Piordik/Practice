#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env"

if [ -f "$ENV_FILE" ]; then
    source "$ENV_FILE"
else
    echo "Файл .env не найден."
fi

# ====================== Настройки ======================
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}
DB_USER=${DB_USER:-postgres}
DB_NAME=${DB_NAME:-postgres}
DB_PASSWORD=${DB_PASSWORD:-postgres}

BACKUP_DIR=${BACKUP_DIR:-"./backups"}
BACKUP_FILE="$BACKUP_DIR/backup_$(date +'%Y%m%d_%H%M%S').sql"

mkdir -p "$BACKUP_DIR"
export PGPASSWORD="$DB_PASSWORD"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*"
}

backup_db() {
    log "Создание backup базы данных '$DB_NAME'..."
    pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -F c -f "$BACKUP_FILE"
    log "Backup создан: $BACKUP_FILE"
}

restore_db() {
    local file=${1:-$BACKUP_FILE}
    if [ ! -f "$file" ]; then
        echo "Файл бэкапа не найден: $file"
        exit 1
    fi

    log "Восстановление базы из $file..."
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "DROP DATABASE IF EXISTS \"$DB_NAME\";" >/dev/null 2>&1
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "CREATE DATABASE \"$DB_NAME\";" >/dev/null 2>&1
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$file"
    log "База успешно восстановлена"
}

case "$1" in
    backup)  backup_db ;;
    restore) restore_db "$2" ;;
    reset|setup) restore_db "$2" ;;
    *) 
        echo "Использование: $0 {backup|restore|reset} [file]"
        exit 1 
        ;;
esac

unset PGPASSWORD