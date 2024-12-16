#!/bin/bash

docker-compose -f docker-compose.yml -f assistant_dists/dream_voice/docker-compose.override.yml -f assistant_dists/dream_voice/dev.yml -f assistant_dists/dream_voice/proxy.yml exec voice-service bash tests/test_voice_service.sh