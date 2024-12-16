cd ../../

docker-compose -f docker-compose.yml \
 -f assistant_dists/dream_ranking_and_midas_based_dm/docker-compose.override.yml \
 -f assistant_dists/dream_ranking_and_midas_based_dm/proxy.yml \
 -f assistant_dists/dream_ranking_and_midas_based_dm/dev.yml up --detach --build --force-recreate

echo "Service is up"
sleep 5
python /home/losta15/losta15/GL_dream/response_selectors/ranking_and_intent_based_response_selector/test_data_quality.py

docker-compose -f docker-compose.yml \
-f assistant_dists/dream_ranking_and_midas_based_dm/docker-compose.override.yml \
-f assistant_dists/dream_ranking_and_midas_based_dm/proxy.yml \
-f assistant_dists/dream_ranking_and_midas_based_dm/dev.yml \
down