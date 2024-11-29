import requests
import logging
import os
import time
from flask import Flask, request, jsonify
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from reader import Reader


FACT_CLS_PORT = 8087
FACT_RETRIEVAL_PORT = 8100

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

    fact_titles = [[fact.split(";")[0].strip() if len(fact.split(";")) > 1 else fact for fact in facts] for facts in top_facts]
    logger.info(fact_titles)

    fact_texts = [[fact.split(";")[1].strip() if len(fact.split(";")) > 1 else fact for fact in facts] for facts in top_facts]

    logger.info(fact_texts)

    qa_res = [["", ""] for i in range(len(questions))]
    try:
        tm_st = time.time()
        for i, question in enumerate(questions):
            answer, reference_passage = reader.answer_question(question, fact_titles[i], fact_texts[i])
            qa_res[i] = [answer, reference_passage]
        logger.info(f"text_qa exec time: {time.time() - tm_st}")
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)
    return jsonify(qa_res)


@app.route("/answer_question", methods=["POST"])
def answer_question():
    questions = request.json.get("question_raw", [" "])
    
    response_factoid = requests.post("http://combined-classification:{}/model".format(FACT_CLS_PORT), json={"sentences": questions}).json()
    top_facts = requests.post("http://fact-retrieval:{}/model".format(FACT_RETRIEVAL_PORT), json = {"human_sentences": questions}).json()
    
    logger.info(response_factoid)
    logger.info(top_facts)

    fact_titles = [[fact.split(";")[0].strip() if len(fact.split(";")) > 1 else fact for fact in facts] for facts in top_facts]
    fact_texts = [[fact.split(";")[1].strip() if len(fact.split(";")) > 1 else fact for fact in facts] for facts in top_facts]
    logger.info(fact_titles)

    qa_res = [{"annotation": response_factoid[i]['factoid_classification'], "answer": "", "reference_passage": ""} for i in range(len(questions))]
    try:
        tm_st = time.time()
        for i, question in enumerate(questions):
            logger.info(response_factoid[i]['factoid_classification']['is_factoid'])
            logger.info(fact_titles[i])
            logger.info(fact_texts[i])
            if response_factoid[i]['factoid_classification']['is_factoid'] > 0.8:
                answer, reference_passage = reader.answer_question(question, fact_titles[i], fact_texts[i])
                qa_res[i]["answer"] = answer
                qa_res[i]["reference_passage"] = reference_passage
        logger.info(f"text_qa exec time: {time.time() - tm_st}")
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)
    return jsonify(qa_res)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)


