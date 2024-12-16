#!/bin/bash

docker-compose -f docker-compose.yml -f assistant_dists/dream_ocean/docker-compose.override.yml -f assistant_dists/dream_ocean/dev.yml -p bot_test up --build -d personality-detection
cd annotators/personality_detection
python test_launch_time.py
python test_time.py
python test_format.py
python test_accuracy.py
cd ../../
docker-compose -f docker-compose.yml -f assistant_dists/dream_ocean/docker-compose.override.yml -f assistant_dists/dream_ocean/dev.yml -p bot_test down