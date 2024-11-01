#!/bin/bash
cd ../../

{ time docker-compose -f docker-compose.yml \
  -f assistant_dists/dream_ranking_and_sf_based_dm/docker-compose.override.yml \
  -f assistant_dists/dream_ranking_and_sf_based_dm/dev.yml \
  up --detach --build speech-function-classifier; } 2> time_output.txt

echo "Service is up"
sleep 5  

real_time=$(grep "real" time_output.txt | awk '{print $2}')
echo "Real time extracted: $real_time"

python annotators/speech_function_classifier/test_launch_time.py "$real_time"

docker-compose -f docker-compose.yml \
  -f assistant_dists/dream_ranking_and_sf_based_dm/docker-compose.override.yml \
  -f assistant_dists/dream_ranking_and_sf_based_dm/dev.yml \
  down