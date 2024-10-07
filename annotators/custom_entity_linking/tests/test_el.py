import os
import time
from pathlib import Path
import requests
from dotenv import load_dotenv
from deeppavlov_kg import TerminusdbKnowledgeGraph


load_dotenv("./.env")

INDEX_LOAD_PATH = Path(os.path.expanduser("~/.deeppavlov/downloads/entity_linking_eng/custom_el_eng_dream"))
TERMINUSDB_SERVER_URL = "http://0.0.0.0:6363"
TERMINUSDB_SERVER_TEAM = "admin"
TERMINUSDB_SERVER_DB = "user_knowledge_db"
TERMINUSDB_SERVER_PASSWORD = "root"


graph = TerminusdbKnowledgeGraph(
    db_name=TERMINUSDB_SERVER_DB,
    team=TERMINUSDB_SERVER_TEAM,
    server=TERMINUSDB_SERVER_URL,
    password=TERMINUSDB_SERVER_PASSWORD,
    index_load_path=INDEX_LOAD_PATH,
)


def main():
    st_time = time.time()
    url = "http://0.0.0.0:8153"
    inserted_data = {
        "user_id": "User/Jack",
        "entity_info": {
            "entity_substr": ["forrest gump"],
            "entity_ids": ["film/123"],
            "tags": ["film"],
        },
    }
    graph.index.set_active_user_id(inserted_data["user_id"])
    graph.index.add_entities(
        inserted_data["entity_info"]["entity_substr"],
        inserted_data["entity_info"]["entity_ids"],
        inserted_data["entity_info"]["tags"],
    )

    request_data = [
        {
            "user_id": ["User/Jack"],
            "entity_substr": [["forrest gump"]],
            "entity_tags": [[[("film", 1.0)]]],
            "contexts": [["who directed forrest gump?"]],
        }
    ]
    gold_results = [["film/123"]]

    count = 0
    for data, gold_result in zip(request_data, gold_results):
        result = requests.post(f"{url}/model", json=data)
        try:
            result = result.json()
            print("Success. Test for input-output data in JSON-format passed.")
        except Exception:
            print("Input-output data is not in JSON-format.")
        print(result)
        entity_ids = []
        for entity_info_list in result:
            for entity_info in entity_info_list:
                entity_ids = entity_info.get("entity_ids")
        if entity_ids == gold_result:
            count += 1
        else:
            print(f"Got {result}, but expected: {gold_result}")

    assert count == len(request_data)
    total_time = time.time() - st_time
    print("Success")
    print(f"custom entity linking exec time = {total_time:.3f}s")


if __name__ == "__main__":
    main()
