#!/bin/bash

set -euo pipefail
trap 'echo -e "\033[0;31m❌ Error occurred. Exiting...\033[0m"; exit 1' ERR

# Constants
CONTAINERS=("Speak2Summary-flask" "Speak2Summary-celery" "Speak2Summary-redis")
COMPOSE_FILE="docker-compose.yml"

log() {
    echo -e "\033[1;34m[INFO]\033[0m $*"
}

stop_and_remove_containers() {
    log "Stopping and removing containers if they exist..."
    for container in "${CONTAINERS[@]}"; do
        if docker ps -a --format '{{.Names}}' | grep -qw "$container"; then
            docker stop "$container" >/dev/null 2>&1 || true
            docker rm "$container" >/dev/null 2>&1 || true
            log "✅ Removed $container"
        else
            log "⏭️  Container $container does not exist. Skipping..."
        fi
    done
}



start_docker_compose() {
    if [[ -f "$COMPOSE_FILE" ]]; then
        docker compose up --build -d
    else
        echo -e "\033[0;31m❌ Compiled code or docker-compose.yml not found.\033[0m"
        exit 1
    fi
}

cleanup() {
    log "Cleaning up compiled directory..."
    rm -rf "$COMPILED_DIR"
}

# ------------------ MAIN ------------------

log "🚀 Starting Speak2Summary deployment..."
stop_and_remove_containers
start_docker_compose
# ping the :5000/health endpoint to ensure the service is up
log "🎉 Speak2Summary started and cleaned up successfully!"
