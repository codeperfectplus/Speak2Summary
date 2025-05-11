#!/bin/bash

# Load from bashrc
source ~/.bashrc

# Export to .env file for Docker Compose
echo "GROQ_API_KEY=$GROQ_API_KEY" > .env

docker-compose down --volumes --remove-orphans
# Start containers
docker-compose up --build

