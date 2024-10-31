#!/bin/bash

docker-compose -f docker-compose.yml -f assistant_dists/dream/docker-compose.override.yml -f assistant_dists/dream/dev.yml up  --detach --build fact-retrieval text-qa combined-classification > build.log 2>&1
# source venv/bin/activate
pytest -s --log-cli-level=INFO tests/test_text_qa_full_pipeline.py | tee tests.log
docker-compose -f docker-compose.yml -f assistant_dists/dream/docker-compose.override.yml -f assistant_dists/dream/dev.yml down > service_stopping.log 2>&1