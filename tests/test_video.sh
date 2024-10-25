#!/bin/bash

docker-compose -f docker-compose.yml -f assistant_dists/dream_multimodal/docker-compose.override.yml -f assistant_dists/dream_multimodal/dev.yml -f assistant_dists/dream_multimodal/proxy.yml exec -it vidchapters-service bash tests/test_video.sh