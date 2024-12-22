#!/bin/bash

cd ../../ && docker-compose -f docker-compose.yml -f assistant_dists/dream_emotion/docker-compose.override.yml -f assistant_dists/dream_emotion/dev.yml -p bot_test up --build -d openai-api-chatgpt emotional-bot-response
sleep 5