#!/bin/bash

TEST_DB_HOST="localhost"
TEST_DB_PORT="5432"
TEST_DB_USER="postgres"
TEST_DB_NAME="postgres"
TEST_DB_PASSWORD="postgres"

BACKUP_FILE="/var/backups/postgresql/backup.sql"

export PGPASSWORD="$TEST_DB_PASSWORD"

echo "[$(date +'%Y-%m-%d %H:%M:%S')] $BACKUP_FILE"

psql -h "$TEST_DB_HOST" -p "$TEST_DB_PORT" -U "$TEST_DB_USER" -d postgres -c "DROP DATABASE IF EXISTS $TEST_DB_NAME;"
psql -h "$TEST_DB_HOST" -p "$TEST_DB_PORT" -U "$TEST_DB_USER" -d postgres -c "CREATE DATABASE $TEST_DB_NAME;"

psql -h "$TEST_DB_HOST" -p "$TEST_DB_PORT" -U "$TEST_DB_USER" -d "$TEST_DB_NAME" -f "$BACKUP_FILE"

unset PGPASSWORD