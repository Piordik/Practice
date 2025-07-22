#!/bin/bash

COMPOSE_FILE="docker-compose.yml"
SERVICE_NAME="app"
GIT_REPO="https://github.com/Piordik/Practice.git"
GIT_BRANCH="main"
PROJECT_DIR="/home/pva/Practice"

cd "$PROJECT_DIR" || { echo "Failed to get to $PROJECT_DIR"; exit 1; }

echo "=== Start ==="
echo "Time: $(date)"
echo "Current branch: $GIT_BRANCH"

echo "Stopping $SERVICE_NAME..."
docker-compose -f "$COMPOSE_FILE" stop "$SERVICE_NAME"

echo "Updating git rep..."
git fetch origin
git checkout "$GIT_BRANCH"
git pull origin "$GIT_BRANCH"

if [ $? -ne 0 ]; then
    echo "Update error."
    exit 1
fi

echo "Building image $SERVICE_NAME..."
docker-compose -f "$COMPOSE_FILE" build "$SERVICE_NAME"

if [ $? -ne 0 ]; then
    echo "Build error."
    exit 1
fi

echo "Launching service $SERVICE_NAME..."
docker-compose -f "$COMPOSE_FILE" up -d --no-deps --build "$SERVICE_NAME"

SERVICE_STATUS=$(docker-compose -f "$COMPOSE_FILE" ps -q "$SERVICE_NAME" | xargs docker inspect -f '{{.State.Status}}')

if [ "$SERVICE_STATUS" == "running" ]; then
    echo "=== Deploy completed ==="
    echo "Service $SERVICE_NAME working"
    echo "Время: $(date)"
else
    echo "=== Deploy error ==="
    echo "Service $SERVICE_NAME isnt working"
    echo "Status: $SERVICE_STATUS"
    exit 1
fi