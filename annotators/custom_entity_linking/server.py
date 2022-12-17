import logging
import os
import time
from flask import Flask, request, jsonify
import sentry_sdk
from deeppavlov import build_model

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
sentry_sdk.init(os.getenv("SENTRY_DSN"))

app = Flask(__name__)

config_name = os.getenv("CONFIG")

try:
    el = build_model(config_name, download=True)
    logger.info("model loaded")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e


@app.route("/add_entities", methods=["POST"])
def add_entities():
    inp = request.json
    entity_info = inp.get("entity_info", {})
    entity_substr_list = entity_info.get("entity_substr", [])
    entity_ids_list = entity_info.get("entity_ids", [])
    tags_list = entity_info.get("tags", [])
    el[0].add_custom_entities(entity_substr_list, entity_ids_list, tags_list)
    logger.info(f"added entities {entity_info}")


@app.route("/model", methods=["POST"])
def respond():
    st_time = time.time()
    inp = request.json
    custom_entity_substr_batch = inp.get("custom_entity_substr", [])
    custom_entity_ids_batch = inp.get("custom_entity_ids", [])
    custom_entity_tags_batch = inp.get("custom_entity_tags", [])
    for entity_substr_list, entity_ids_list, entity_tags_list in \
            zip(custom_entity_substr_batch, custom_entity_ids_batch, custom_entity_tags_batch):
        el[0].add_custom_entities(entity_substr_list, entity_ids_list, entity_tags_list)
    
    entity_substr_batch = inp.get("entity_substr", [[""]])
    entity_tags_batch = inp.get(
        "entity_tags", [["" for _ in entity_substr_list] for entity_substr_list in entity_substr_batch]
    )
    context_batch = inp.get("context", [[""]])
    opt_context_batch = []
    for hist_utt in context_batch:
        hist_utt = [utt for utt in hist_utt if len(utt) > 1]
        last_utt = hist_utt[-1]
        if last_utt[-1] not in {".", "!", "?"}:
            last_utt = f"{last_utt}."
        if len(hist_utt) > 1:
            prev_utt = hist_utt[-2]
            if prev_utt[-1] not in {".", "!", "?"}:
                prev_utt = f"{prev_utt}."
            opt_context_batch.append([prev_utt, last_utt])
        else:
            opt_context_batch.append([last_utt])

    entity_info_batch = [[{}] for _ in entity_substr_batch]
    try:
        (
            entity_substr_batch,
            entity_ids_batch,
            conf_batch,
            entity_id_tags_batch,
        ) = el(entity_substr_batch, entity_tags_batch, opt_context_batch)
        entity_info_batch = []
        for (
            entity_substr_list,
            entity_ids_list,
            conf_list,
            entity_id_tags_list,
        ) in zip(
            entity_substr_batch,
            entity_ids_batch,
            conf_batch,
            entity_id_tags_batch,
        ):
            entity_info_list = []
            for entity_substr, entity_ids, confs, entity_id_tags in zip(
                entity_substr_list,
                entity_ids_list,
                conf_list,
                entity_id_tags_list,
            ):
                entity_info = {}
                entity_info["entity_substr"] = entity_substr
                entity_info["entity_ids"] = entity_ids
                entity_info["confidences"] = [float(elem[2]) for elem in confs]
                entity_info["tokens_match_conf"] = [float(elem[0]) for elem in confs]
                entity_info["entity_id_tags"] = entity_id_tags
                entity_info_list.append(entity_info)
            entity_info_batch.append(entity_info_list)
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)
    total_time = time.time() - st_time
    logger.info(f"custom entity linking exec time = {total_time:.3f}s")
    return jsonify(entity_info_batch)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
