#!/bin/bash

set -euo pipefail
trap 'echo -e "\033[0;31m❌ Error occurred. Exiting...\033[0m"; exit 1' ERR

# Constants
CONTAINERS=("transmeet-flask" "transmeet-celery" "transmeet-redis")
COMPILE_SCRIPT="./compile_code.sh"
COMPILED_DIR="./compiled_code"
COMPOSE_FILE="$COMPILED_DIR/docker-compose.yml"

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

run_compile_script() {
    if [[ -f "$COMPILE_SCRIPT" ]]; then
        log "Running compile script..."
        bash "$COMPILE_SCRIPT"
    else
        echo -e "\033[0;31m❌ Compile script not found: $COMPILE_SCRIPT\033[0m"
        exit 1
    fi
}

start_docker_compose() {
    if [[ -d "$COMPILED_DIR" && -f "$COMPOSE_FILE" ]]; then
        log "Starting Docker Compose from compiled directory..."
        pushd "$COMPILED_DIR" > /dev/null
        docker compose up --build -d
        popd > /dev/null
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

log "🚀 Starting Transmeet deployment..."

stop_and_remove_containers
run_compile_script
# go to compiled_code directory and run the compile script
start_docker_compose

# ping the :5000/health endpoint to ensure the service is up
log "🎉 Transmeet started and cleaned up successfully!"
