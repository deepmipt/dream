cd ../../

{ time docker-compose -f docker-compose.yml \
    -f assistant_dists/dream_ranking_and_sf_based_dm/docker-compose.override.yml \
    -f assistant_dists/dream_ranking_and_sf_based_dm/proxy.yml \
    -f assistant_dists/dream_ranking_and_sf_based_dm/dev.yml up --detach --build --force-recreate; } 2> time_output.txt

echo "Service is up"
sleep 5
real_time=$(grep "real" time_output.txt | awk '{print $2}')

python response_selectors/ranking_and_sf_based_response_selector/test_launch_time.py "$real_time"

docker-compose -f docker-compose.yml \
-f assistant_dists/dream_ranking_and_sf_based_dm/docker-compose.override.yml \
-f assistant_dists/dream_ranking_and_sf_based_dm/proxy.yml \
-f assistant_dists/dream_ranking_and_sf_based_dm/dev.yml \
down