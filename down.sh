#!/bin/bash

source .env

if [ "$MODE" = "DEV" ]; then
  sudo docker-compose -f docker-compose_dev.yml down
elif [ "$MODE" = "STAGE" ]; then
  sudo docker-compose -f docker-compose_stage.yml down
elif [ "$MODE" = "PROD" ]; then
  sudo docker-compose -f docker-compose_prod.yml down
else
  echo "Unknown MODE: $MODE"
  exit 1
fi
