#!/bin/bash

DB_HOST="localhost"
DB_PORT="5432"
DB_USER="postgres"
DB_NAME="postgres"
DB_PASSWORD="2501"

BACKUP_DIR="/home/pva/Practice/Scripts/backups"

BACKUP_FILE="$BACKUP_DIR/backup.sql"

mkdir -p "$BACKUP_DIR"

export PGPASSWORD="$DB_PASSWORD"

echo "[$(date +'%Y-%m-%d %H:%M:%S')] $DB_NAME"

pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$BACKUP_FILE"

unset PGPASSWORD