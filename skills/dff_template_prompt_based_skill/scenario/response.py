import json
import logging
import re
import requests
import sentry_sdk
from os import getenv
from typing import Any

import common.dff.integration.context as int_ctx
import common.dff.integration.response as int_rsp
from common.constants import CAN_NOT_CONTINUE
from df_engine.core import Context, Actor
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize


sentry_sdk.init(getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
GENERATIVE_SERVICE_URL = getenv("GENERATIVE_SERVICE_URL")
PROMPT_FILE = getenv("PROMPT_FILE")
assert GENERATIVE_SERVICE_URL
assert PROMPT_FILE

with open(PROMPT_FILE, "r") as f:
    PROMPT = json.load(f)["prompt"]

FIX_PUNCTUATION = re.compile(r"\s(?=[\.,:;])")
GENERATIVE_TIMEOUT = 4
DEFAULT_CONFIDENCE = 0.9
LOW_CONFIDENCE = 0.5


def compose_data_for_model(ctx, actor):
    global PROMPT
    text_prompt = []
    stop_words = set(stopwords.words("english"))
    human_uttrs = int_ctx.get_human_utterances(ctx, actor)
    bot_uttrs = int_ctx.get_bot_utterances(ctx, actor)
    if len(human_uttrs) > 0:
        logger.info(f"utts: {human_uttrs[-1]}")
        text_prompt.append(f'Human: {human_uttrs[-1]["text"]}')
        if len(bot_uttrs) > 0:
            text_prompt.insert(0, f'AI: {bot_uttrs[-1]["text"]}')
        if len(human_uttrs) > 1:
            text_prompt.insert(0, f'Human: {human_uttrs[-2]["text"]}')
            text_prompt.insert(0, PROMPT)
        words = word_tokenize(human_uttrs[-1]["text"])
        words_filtered = []
        for w in words:
            if w not in stop_words:
                words_filtered.append(w)
    logger.info(f"prompt: {text_prompt}")
    if text_prompt:
        text_prompt = [re.sub(FIX_PUNCTUATION, "", x) for x in text_prompt]  # костыль
    return text_prompt


def generative_response(ctx: Context, actor: Actor, *args, **kwargs) -> Any:
    curr_responses, curr_confidences, curr_human_attrs, curr_bot_attrs, curr_attrs = (
        [],
        [],
        [],
        [],
        [],
    )

    def gathering_responses(reply, confidence, human_attr, bot_attr, attr):
        nonlocal curr_responses, curr_confidences, curr_human_attrs, curr_bot_attrs, curr_attrs
        if reply and confidence:
            curr_responses += [reply]
            curr_confidences += [confidence]
            curr_human_attrs += [human_attr]
            curr_bot_attrs += [bot_attr]
            curr_attrs += [attr]

    request_data = compose_data_for_model(ctx, actor)
    logger.info(f"request_data: {request_data}")
    if len(request_data) > 0:
        response = requests.post(
            GENERATIVE_SERVICE_URL,
            json={"dialog_context": [request_data]},
            timeout=GENERATIVE_TIMEOUT,
        )
        hypotheses = response.json()
    else:
        hypotheses = []
    logger.info(f"hyps: {hypotheses}")
    if hypotheses:
        for hyp in hypotheses:
            confidence = DEFAULT_CONFIDENCE
            hyp_text = " ".join(hyp[0].split())
            if len(hyp_text) and hyp_text[-1] not in [".", "?", "!"]:
                hyp_text += "."
                confidence = LOW_CONFIDENCE
            gathering_responses(hyp_text, confidence, {}, {}, {"can_continue": CAN_NOT_CONTINUE})

    if len(curr_responses) == 0:
        return ""
    return int_rsp.multi_response(
        replies=curr_responses,
        confidences=curr_confidences,
        human_attr=curr_human_attrs,
        bot_attr=curr_bot_attrs,
        hype_attr=curr_attrs,
    )(ctx, actor, *args, **kwargs)
