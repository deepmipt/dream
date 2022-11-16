import logging
import os
import time

from flask import Flask, request, jsonify
import sentry_sdk

from sentry_sdk.integrations.flask import FlaskIntegration
from deeppavlov import build_model
from common.utils import combined_classes

logger = logging.getLogger(__name__)
sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])

app = Flask(__name__)


def get_result(sentences, sentences_with_history, postannotations=False):
    logger.debug((sentences, sentences_with_history, postannotations))
    ans = [{} for _ in sentences]
    if not sentences:
        logger.exception("Input sentences not received")
        sentences = [" "]
    if not sentences_with_history:
        logger.exception("Input sentences with history not received")
        sentences_with_history = sentences
    if not postannotations:
        data = [
            sentences,  # emo was trained without history
            sentences,  # sentiment was trained without history
            sentences,  # toxic was trained without history
            sentences,  # factoid was trained without history
            sentences_with_history,  # midas was trained with history
            sentences,  # deeppavlov topics was trained without history
            sentences,  # cobot topics was trained without history
            sentences,  # cobot dialogact topics is now trained without history
            sentences,  # cobot dialogact intents is now trained without history
        ]
    else:
        # While using postannotations, we annotate only for tasks we use in response_selector
        data = [[] for _ in range(9)]
        data[2] = sentences
        data[-1] = sentences
        data[-2] = sentences
        data[-3] = sentences
    try:
        prob_lists = model(*data)
        for task_name, prob_list in zip(combined_classes, prob_lists):
            for i in range(len(prob_list)):
                if len(prob_list[i]):
                    is_toxic = "toxic" in task_name and prob_list[i][-1] < 0.5
                    if is_toxic:  # sum of probs of all toxic classes >0.5
                        prob_list[i][-1] = 0
                        prob_list[i] = [k / sum(prob_list[i]) for k in prob_list[i]]
                    ans[i][task_name] = {
                        class_: round(float(prob), 2) for class_, prob in zip(combined_classes[task_name], prob_list[i])
                    }
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)

    return ans


try:
    model = build_model("combined_classifier.json", download=False)
    logger.info("Making test res")
    test_res = get_result(["a"], ["a"])
    logger.info("model loaded, test query processed")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e


@app.route("/model", methods=["POST"])
def respond():
    t = time.time()
    sentences = request.json.get("sentences", [" "])
    sentences_with_hist = request.json.get("sentences_with_history", sentences)
    answer = get_result(sentences, sentences_with_hist, postannotations=False)
    logger.debug(f"combined_classification result: {answer}")
    logger.info(f"combined_classification exec time: {time.time() - t}")
    return jsonify(answer)


@app.route("/batch_model", methods=["POST"])
def batch_respond():
    t = time.time()
    sep = " [SEP] "
    utterances_with_histories = request.json.get("utterances_with_histories", [[" "]])
    sentences_with_hist = [sep.join(s) for s in utterances_with_histories]
    sentences = [s[-1].split(sep)[-1] for s in utterances_with_histories]
    answer = get_result(sentences, sentences_with_hist, postannotations=True)
    logger.debug(f"combined_classification batch result: {answer}")
    logger.info(f"combined_classification exec time: {time.time() - t}")
    return jsonify([{"batch": answer}])


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
