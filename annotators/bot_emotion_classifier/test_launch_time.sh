#!/bin/bash

cd ../../ && docker-compose -f docker-compose.yml -f assistant_dists/dream_emotion/docker-compose.override.yml -f assistant_dists/dream_emotion/dev.yml -p bot_test up --build -d bot-emotion-classifier
python annotators/bot_emotion_classifier/test_launch_time.py
docker-compose -f docker-compose.yml -f assistant_dists/dream_emotion/docker-compose.override.yml -f assistant_dists/dream_emotion/dev.yml -p bot_test down