import requests
import json
import re
from deeppavlov_kg import TerminusdbKnowledgeGraph


def formulate_utt_annotations(dog_id=None, park_id=None):
    utt_annotations = {
        "property_extraction": [
            {
                "triplets": [
                    {"subject": "user", "relation": "HAVE PET", "object": "dog"},
                    {"subject": "user", "relation": "LIKE GOTO", "object": "park"},
                ]
            }
        ],
        "custom_entity_linking": [],
    }

    # if dog is in kg add it to custom_el annotations
    if dog_id is not None:
        utt_annotations["custom_entity_linking"].append(
            {
                "entity_substr": "dog",
                "entity_ids": [dog_id],
                "confidences": [1.0],
                "tokens_match_conf": [1.0],
                "entity_id_tags": ["Animal"],
            },
        )
    if park_id is not None:
        utt_annotations["custom_entity_linking"].append(
            {
                "entity_substr": "park",
                "entity_ids": [park_id],
                "confidences": [1.0],
                "tokens_match_conf": [1.0],
                "entity_id_tags": ["Place"],
            },
        )

    return utt_annotations


def prepare_for_comparison(results):
    for result in results:
        if uttrs := result["added_to_graph"]:
            for utt in uttrs:
                for triplet in utt:
                    triplet[2] = triplet[2].split("/")[0]
        if uttrs := result["triplets_already_in_graph"]:
            for utt in uttrs:
                for triplet in utt:
                    triplet[2] = triplet[2].split("/")[0]

    return results


def compare_results(results, golden_results) -> bool:
    def compare(uttrs, golden_result):
        for idx, utt in enumerate(uttrs):
            for triplet in utt:
                if triplet not in golden_result[idx]:
                    return False
        return True

    is_successfull = []
    for result, golden_result in zip(results, golden_results):
        is_added = compare(result["added_to_graph"], golden_result["added_to_graph"])
        is_in_graph = compare(result["triplets_already_in_graph"], golden_result["triplets_already_in_graph"])
        is_successfull.append(is_added)
        is_successfull.append(is_in_graph)
    return all(is_successfull)


def get_service_time(pattern, time_result):
    pattern_string = re.search(pattern, time_result.text)[0]
    pattern_dict = json.loads("{" + pattern_string.split(',"children": [{')[0] + "}")

    return pattern_dict["time"]


def main():
    TERMINUSDB_SERVER_URL = "http://0.0.0.0:6363"
    TERMINUSDB_SERVER_TEAM = "admin"
    TERMINUSDB_SERVER_DB = "user_knowledge_db"
    TERMINUSDB_SERVER_PASSWORD = "root"
    USER_KNOWLEDGE_MEMORIZER_PORT = 8027  # tested with dream_kg_prompted distribution

    USER_KNOWLEDGE_MEMORIZER_URL = f"http://0.0.0.0:{USER_KNOWLEDGE_MEMORIZER_PORT}/respond"

    graph = TerminusdbKnowledgeGraph(
        db_name=TERMINUSDB_SERVER_DB,
        team=TERMINUSDB_SERVER_TEAM,
        server=TERMINUSDB_SERVER_URL,
        password=TERMINUSDB_SERVER_PASSWORD,
    )

    USER_ID = "User/b75d2700259bdc44sdsdf85e7f530ed"

    PATTERN_KNOWLEDGE = r"\"function\": \"get_knowledge\".*\"time\": \d.\d+"
    PATTERN_LLM = r"\"function\": \"convert_triplets_to_natural_language\".*\"time\": \d.\d+"
    PATTERN_TERMINUSDB = r"\"function\": \"create_entities\".*\"time\": \d.\d+"
    PATTERN_PROPS = r"\"function\": \"get_properties_of_entities\".*\"time\": \d.\d+"
    # PATTERN_RELS = r"\"function\": \"search_for_relationships\".*\"time\": \d.\d+"
    # get dog_id and park_id from KG
    dog_id, park_id = None, None
    try:
        user_props = graph.get_properties_of_entity(USER_ID)
        entities_info = graph.get_properties_of_entities(
            [*user_props["HAVE PET/Animal"], *user_props["LIKE GOTO/Place"]]
        )
        for entity_info in entities_info:
            if entity_info.get("substr") == "dog":
                dog_id = entity_info["@id"]
            elif entity_info.get("substr") == "park":
                park_id = entity_info["@id"]
        print(f"Found park_id: '{park_id}' and dog_ig: '{dog_id}'")
        added_new_entities = False
    except Exception:
        print("Adding new entities and rels")
        added_new_entities = True

    request_data = [
        {
            "last_human_annotated_utterance": [
                {
                    "text": "i have a dog and a cat",
                    "user": {"id": USER_ID.split("/")[1]},
                    "annotations": formulate_utt_annotations(dog_id, park_id),
                },
                {
                    "text": "",
                    "user": {"id": ""},
                    "annotations": {
                        "property_extraction": [{}],
                        "custom_entity_linking": [],
                    },
                },
            ]
        }
    ]

    golden_triplets = [[[USER_ID, "LIKE GOTO", "Place"], [USER_ID, "HAVE PET", "Animal"]], []]
    if added_new_entities:
        golden_results = [[{"added_to_graph": golden_triplets, "triplets_already_in_graph": [[], []]}]]
    else:
        golden_results = [[{"added_to_graph": [[], []], "triplets_already_in_graph": golden_triplets}]]

    count = 0
    for data, golden_result in zip(request_data, golden_results):
        result = requests.post(USER_KNOWLEDGE_MEMORIZER_URL, json=data)
        try:
            result = result.json()
            print("Success. Test for input-output data in JSON-format passed.")
        except Exception:
            print("Input-output data is not in JSON-format.")
        print(result)
        time_result = requests.post(f"{USER_KNOWLEDGE_MEMORIZER_URL}?profile", json=data)
        output_dict = json.loads(time_result.text)
        # print(output_dict)
        total_time = output_dict["duration"]
        try:
            knowledge_time = get_service_time(PATTERN_KNOWLEDGE, time_result)
            llm_time = get_service_time(PATTERN_LLM, time_result)
            terminusdb_time = get_service_time(PATTERN_TERMINUSDB, time_result)
            props_time = get_service_time(PATTERN_PROPS, time_result)
            exec_time = total_time - knowledge_time - llm_time - terminusdb_time - props_time

        except Exception as e:
            raise e

        result = prepare_for_comparison(result)
        if compare_results(result, golden_result):
            count += 1
    assert count == len(request_data)
    print("Success")
    # print(f"Total time including requests to other services = {total_time:.3f}s")
    print(f"user knowledge memorizer exec time = {exec_time:.3f}s")


if __name__ == "__main__":
    main()
