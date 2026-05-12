#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*"
}

log "Запуск деплоя Counter Service..."

# 1. Бэкап
"$SCRIPT_DIR/db-utils.sh" backup

# 2. Сборка образа
log "Сборка Docker образа..."
docker build -t practice-recovery-app:latest .

# 3. Применение манифестов
log "Применение Kubernetes манифестов..."
kubectl apply -f k8s/

# 4. Перезапуск
log "Перезапуск приложения..."
kubectl rollout restart deployment/app

# 5. Ожидание
log "Ожидание готовности..."
kubectl rollout status deployment/app --timeout=180s

log "Деплой успешно завершён!"