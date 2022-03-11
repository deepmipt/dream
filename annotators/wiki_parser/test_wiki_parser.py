import os
import requests


if os.getenv("LANGUAGE", "EN") == "RU":
    lang = "@ru"
else:
    lang = "@en"


def main():
    url = "http://0.0.0.0:8077/model"

    request_data_en = [
        {
            "parser_info": ["find_top_triplets"],
            "query": [[{"entity_substr": "Jurgen Schmidhuber", "entity_ids": ["Q92735"]}]],
        }
    ]
    request_data_ru = [
        {
            "parser_info": ["find_top_triplets"],
            "query": [[{"entity_substr": "Юрген Шмидхубер", "entity_ids": ["Q92735"]}]],
        }
    ]
    gold_results_en = [
        [
            {
                "animals_skill_entities_info": {},
                "entities_info": {
                    "Jurgen Schmidhuber": {
                        "age": 59,
                        "conf": 1.0,
                        "country of sitizenship": [["Q183", "Germany"]],
                        "date of birth": [['"+1963-01-17^^T"', "17 January 1963"]],
                        "entity_label": "Jürgen Schmidhuber",
                        "instance of": [["Q5", "human"]],
                        "occupation": [
                            ["Q15976092", "artificial intelligence researcher"],
                            ["Q1622272", "university teacher"],
                            ["Q82594", "computer scientist"],
                        ],
                        "plain_entity": "Q92735",
                        "pos": 0,
                        "token_conf": 1.0,
                        "types_2hop": [
                            ["Q14565186", "cognitive scientist"],
                            ["Q66666607", "academic profession"],
                            ["Q5", "human"],
                            ["Q28640", "profession"],
                            ["Q3400985", "academic"],
                            ["Q37226", "teacher"],
                            ["Q41835716", "faculty member"],
                            ["Q1622272", "university teacher"],
                            ["Q82594", "computer scientist"],
                            ["Q15976092", "artificial intelligence researcher"],
                            ["Q901", "scientist"],
                        ],
                    }
                },
                "topic_skill_entities_info": {},
                "utt_num": 0,
                "wiki_skill_entities_info": {},
            }
        ]
    ]
    gold_results_ru = [
        [
            {
                "animals_skill_entities_info": {},
                "entities_info": {
                    "Юрген Шмидхубер": {
                        "age": 59,
                        "conf": 1.0,
                        "country of sitizenship": [["Q183", "Германия"]],
                        "date of birth": [['"+1963-01-17^^T"', "17 January 1963"]],
                        "entity_label": "Шмидхубер, Юрген",
                        "instance of": [["Q5", "человек"]],
                        "occupation": [
                            ["Q15976092", "исследователь искусственного интеллекта"],
                            ["Q1622272", "преподаватель университета"],
                            ["Q82594", "специалист в области информатики"],
                        ],
                        "plain_entity": "Q92735",
                        "pos": 0,
                        "token_conf": 1.0,
                        "types_2hop": [
                            ["Q15976092", "исследователь искусственного интеллекта"],
                            ["Q1622272", "преподаватель университета"],
                            ["Q28640", "профессия"],
                            ["Q3400985", "научный работник"],
                            ["Q37226", "учитель"],
                            ["Q41835716", "преподаватель"],
                            ["Q5", "человек"],
                            ["Q66666607", "академическая профессия"],
                            ["Q82594", "специалист в области информатики"],
                            ["Q901", "учёный"],
                        ],
                    }
                },
                "topic_skill_entities_info": {},
                "utt_num": 0,
                "wiki_skill_entities_info": {},
            }
        ]
    ]

    count = 0
    if lang == "@ru":
        for data, gold_result in zip(request_data_ru, gold_results_ru):
            result = requests.post(url, json=data).json()
            if result == gold_result:
                count += 1
        assert count == len(request_data_ru), print(f"Got {result}, but expected: {gold_result}")

        print("Success")
    elif lang == "@en":
        for data, gold_result in zip(request_data_en, gold_results_en):
            result = requests.post(url, json=data).json()
            if result == gold_result:
                count += 1
        assert count == len(request_data_en), print(f"Got {result}, but expected: {gold_result}")

        print("Success")


if __name__ == "__main__":
    main()
