import json
import logging
import nltk
import os
import pickle
import re
import time

import numpy as np
import sentry_sdk
from flask import Flask, request, jsonify
from sentry_sdk.integrations.flask import FlaskIntegration
from deeppavlov import build_model

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])

CONFIG = os.getenv("CONFIG")

try:
    fact_retrieval = build_model(CONFIG, download=True)

except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e

app = Flask(__name__)

@app.route("/model", methods=["POST"])
def respond():
    st_time = time.time()
    cur_utt = request.json.get("human_sentences", [" "])
    dialog_history = request.json.get("dialog_history", [" " for _ in cur_utt])
    cur_utt = [utt.lstrip("alexa") for utt in cur_utt]

    logger.info(f"cur_utt {cur_utt}")


    nf_numbers, f_utt, f_dh = [], [], []
    for n, (utt, dh) in enumerate(zip(cur_utt, dialog_history)):
        f_utt.append(utt)
        f_dh.append(dh)

    out_res = [[] for _ in cur_utt]
    try:
        logger.info(f"f_utt {f_utt}")
        if f_utt:
            fact_res = fact_retrieval(f_utt) if len(f_utt[0].split()) > 3 else fact_retrieval(f_dh)
            logger.info(f"fact_res {fact_res}")
            if fact_res:
                out_res = [[fact[0].replace('""', '"')  + "; " + fact[1].replace('""', '"') for fact in facts] for facts in fact_res]

            logger.info(f"output titles and facts {out_res}")

    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)
    total_time = time.time() - st_time
    logger.info(f"fact_retrieval exec time: {total_time:.3f}s")
    return jsonify(out_res)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
