#!/bin/bash

docker-compose -f docker-compose.yml -f assistant_dists/dream_emotion/docker-compose.override.yml -f assistant_dists/dream_emotion/dev.yml -p bot_test up --build -d bot-emotion-classifier
cd annotators/bot_emotion_classifier
python test_launch_time.py
python test_time.py
python test_format.py
cd ../../
docker-compose -f docker-compose.yml -f assistant_dists/dream_emotion/docker-compose.override.yml -f assistant_dists/dream_emotion/dev.yml -p bot_test down