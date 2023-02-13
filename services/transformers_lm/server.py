import logging
import json
import os
import time

import sentry_sdk
import torch
from flask import Flask, request, jsonify
from sentry_sdk.integrations.flask import FlaskIntegration
from transformers import AutoModelForCausalLM, AutoTokenizer

sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

PRETRAINED_MODEL_NAME_OR_PATH = os.environ.get("PRETRAINED_MODEL_NAME_OR_PATH")
CONFIG_NAME = os.environ.get("CONFIG_NAME")
HALF_PRECISION = bool(int(os.environ.get("HALF_PRECISION", 0)))
logging.info(f"PRETRAINED_MODEL_NAME_OR_PATH = {PRETRAINED_MODEL_NAME_OR_PATH}")
NAMING = ["AI", "Human"]
MAX_LEN_GEN_TEXT = os.environ.get("MAX_LEN_GEN_TEXT", 0)

with open(CONFIG_NAME, "r") as f:
    generation_params = json.load(f)
if not MAX_LEN_GEN_TEXT:
    max_length = generation_params.get("max_length", 50)
else:
    max_length = int(MAX_LEN_GEN_TEXT)
del generation_params["max_length"]

app = Flask(__name__)
logging.getLogger("werkzeug").setLevel("WARNING")


def generate_responses(context, model, tokenizer, prompt, continue_last_uttr=False):
    outputs = []
    dialog_context = ""
    if prompt:
        dialog_context += prompt + "\n"
    s = len(context) % 2
    context = [
        f"{NAMING[(s + uttr_id) % 2]}: {uttr}" for uttr_id, uttr in enumerate(context)
    ]
    if continue_last_uttr:
        dialog_context += "\n".join(context)
    else:
        dialog_context += "\n".join(context) + f"\n{NAMING[0]}:"

    logger.info(f"context inside generate_responses seen as: {dialog_context}")
    bot_input_ids = tokenizer([dialog_context], return_tensors="pt").input_ids
    with torch.no_grad():
        if torch.cuda.is_available():
            bot_input_ids = bot_input_ids.to("cuda")
        chat_history_ids = model.generate(
            bot_input_ids,
            max_length=len(tokenizer(dialog_context)["input_ids"]) + max_length,
            pad_token_id=tokenizer.eos_token_id,
            **generation_params,
        )
    if torch.cuda.is_available():
        chat_history_ids = chat_history_ids.cpu()
    for result in chat_history_ids:
        output = tokenizer.decode(result, skip_special_tokens=True)
        result_cut = output.replace(dialog_context + " ", "").split("\n")[0]
        logger.info(f"hypothesis: {result_cut}")
        outputs.append(result_cut)
    return outputs


try:
    tokenizer = AutoTokenizer.from_pretrained(PRETRAINED_MODEL_NAME_OR_PATH)
    if HALF_PRECISION:
        model = AutoModelForCausalLM.from_pretrained(
            PRETRAINED_MODEL_NAME_OR_PATH, torch_dtype=torch.float16
        )
    else:
        model = AutoModelForCausalLM.from_pretrained(PRETRAINED_MODEL_NAME_OR_PATH)
    if torch.cuda.is_available():
        model.to("cuda")
        logger.info("transformers_lm is set to run on cuda")
    example_response = generate_responses(
        ["What is the goal of SpaceX?"], model, tokenizer, "You are a SpaceX Assistant."
    )
    logger.info(f"example response: {example_response}")
    logger.info("transformers_lm is ready")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e


@app.route("/ping", methods=["POST"])
def ping():
    return "pong"


@app.route("/respond", methods=["POST"])
def respond():
    st_time = time.time()
    contexts = request.json.get("dialog_contexts", [])
    prompts = request.json.get("prompts", [])
    if len(contexts) > 0 and len(prompts) == 0:
        prompts = [""] * len(contexts)

    try:
        responses = []
        for context, prompt in zip(contexts, prompts):
            curr_responses = []
            outputs = generate_responses(context, model, tokenizer, prompt)
            for response in outputs:
                if len(response) >= 2:
                    curr_responses += [response]
                else:
                    curr_responses += [""]
            responses += [curr_responses]

    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        responses = [[""]] * len(contexts)

    logger.info(f"transformers_lm output: {responses}")
    total_time = time.time() - st_time
    logger.info(f"transformers_lm exec time: {total_time:.3f}s")
    return jsonify(responses)
