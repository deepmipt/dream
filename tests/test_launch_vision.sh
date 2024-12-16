#!/bin/bash

date
docker-compose -f docker-compose.yml -f assistant_dists/dream_multimodal/docker-compose.override.yml -f assistant_dists/dream_multimodal/dev.yml -f assistant_dists/dream_multimodal/proxy.yml build && docker-compose -f docker-compose.yml -f assistant_dists/dream_multimodal/docker-compose.override.yml -f assistant_dists/dream_multimodal/dev.yml -f assistant_dists/dream_multimodal/proxy.yml up --force-recreate
date