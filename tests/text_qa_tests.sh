#!/bin/bash
wget http://files.deeppavlov.ai/chepurova/datasets/NQ-open.dev.jsonl  -O tests/NQ-open.dev.jsonl
touch .env_secret
docker-compose -f docker-compose.yml -f assistant_dists/dream/docker-compose.override.yml -f assistant_dists/dream/dev.yml up  --detach --build fact-retrieval text-qa combined-classification > build.log 2>&1
python3 -m venv test_venv
source test_venv/bin/activate
pip install -r tests/test_text_qa_requirements.txt 
pytest -s --log-cli-level=INFO tests/test_text_qa_full_pipeline.py | tee tests.log
docker-compose -f docker-compose.yml -f assistant_dists/dream/docker-compose.override.yml -f assistant_dists/dream/dev.yml down > service_stopping.log 2>&1