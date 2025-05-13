#!/bin/bash
docker-compose down --volumes --remove-orphans
# Start containers
docker-compose up --build -d

