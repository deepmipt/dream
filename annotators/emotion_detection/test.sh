#!/bin/bash

docker-compose -f docker-compose.yml -f assistant_dists/dream_ocean/docker-compose.override.yml -f assistant_dists/dream_ocean/dev.yml -f assistant_dists/dream_ocean/proxy.yml up --build --force-recreate --detach emotion-detection
python3 annotators/emotion_detection/test_emotion_detection_service.py | tee annotators/emotion_detection/executing_test_emotion_detection_service.txt
# docker-compose -f docker-compose.yml -f assistant_dists/dream_ocean/docker-compose.override.yml -f assistant_dists/dream_ocean/proxy.yml stop emotion-detection