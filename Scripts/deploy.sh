#!/bin/bash

COMPOSE_FILE="docker-compose.yml"
SERVICE_NAME="app"
GIT_REPO="https://github.com/Piordik/Practice.git"
GIT_BRANCH="main"
PROJECT_DIR="/home/pva/Practice"
HEALTH_CHECK_URL="http://localhost:8080/health"
MAX_RETRIES=10
RETRY_INTERVAL=5

cd "$PROJECT_DIR" || { echo "Error getting to the directory $PROJECT_DIR"; exit 1; }

echo "=== Start deploy ==="
echo "Time: $(date)"
echo "Branch: $GIT_BRANCH"

check_health() {
    local retries=0
    echo "Check $HEALTH_CHECK_URL..."
    
    while [ $retries -lt $MAX_RETRIES ]; do
        response=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_CHECK_URL" || true)
        
        if [ "$response" = "200" ]; then
            echo "Success (HTTP 200)"
            return 0
        fi
        
        retries=$((retries+1))
        echo "Try $retries / $MAX_RETRIES: unable to connect (HTTP: ${response:-none})"
        sleep $RETRY_INTERVAL
    done
    
    echo "Healthcheck failed after $MAX_RETRIES tries"
    return 1
}

echo "Stopping $SERVICE_NAME..."
docker-compose -f "$COMPOSE_FILE" stop "$SERVICE_NAME"

echo "Update git rep"
git fetch origin
git checkout "$GIT_BRANCH"
git pull origin "$GIT_BRANCH"

if [ $? -ne 0 ]; then
    echo "Error updating git."
    exit 1
fi

echo "Building image $SERVICE_NAME..."
docker-compose -f "$COMPOSE_FILE" build "$SERVICE_NAME"

if [ $? -ne 0 ]; then
    echo "Building error."
    exit 1
fi

echo "Running $SERVICE_NAME..."
docker-compose -f "$COMPOSE_FILE" up -d --no-deps --build "$SERVICE_NAME"

SERVICE_STATUS=$(docker-compose -f "$COMPOSE_FILE" ps -q "$SERVICE_NAME" | xargs docker inspect -f '{{.State.Status}}')

if [ "$SERVICE_STATUS" != "running" ]; then
    echo "=== Error ==="
    echo "$SERVICE_NAME is stopped"
    echo "Status: $SERVICE_STATUS"
    exit 1
fi

if ! check_health; then
    echo "=== Error ==="
    echo "Service is enabled, but healthcheck failed"
    exit 1
fi

echo "=== Success ==="
echo "Service $SERVICE_NAME is enabled healthcheck is done"
echo "Time: $(date)"