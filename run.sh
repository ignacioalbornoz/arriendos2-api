#!/bin/bash

source .env

if [ "$MODE" = "DEV" ]; then
  sudo docker compose -f docker-compose_dev_mac.yml up --build
elif [ "$MODE" = "STAGE" ]; then
  sudo docker-compose -f docker-compose_stage.yml up --build
elif [ "$MODE" = "PROD" ]; then
  sudo docker-compose -f docker-compose_prod.yml up --build
else
  echo "Unknown MODE: $MODE"
  exit 1
fi
