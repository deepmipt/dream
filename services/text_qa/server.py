import logging
import os
import time
from flask import Flask, request, jsonify
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from reader import Reader

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])

try:
    reader = Reader()
    test_res = reader.answer_question("What is the capital of Russia?", ["Capital of Russia"], ["Moscow is the capital of Russia."])
    logger.info("model loaded, test query processed")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e

app = Flask(__name__)


@app.route("/model", methods=["POST"])
def respond():
    questions = request.json.get("question_raw", [" "])
    top_facts = request.json.get("top_facts", [[" "]])
    logger.info(top_facts)

    fact_titles = [[fact.split(";")[0].strip() for fact in facts] for facts in top_facts]
    logger.info(fact_titles)

    fact_texts = [[fact.split(";")[1].strip() for fact in facts] for facts in top_facts]

    logger.info(fact_texts)

    qa_res = [["", 0.0, 0, ""] for _ in questions]
    try:
        tm_st = time.time()
        for i, question in enumerate(questions):
            qa_res[i] = reader.answer_question(question, fact_titles[i], fact_texts[i])
        logger.info(f"text_qa exec time: {time.time() - tm_st}")
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)
    return jsonify(qa_res)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
