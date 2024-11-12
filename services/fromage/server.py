import logging
import os
import time
import torch
import sentry_sdk
from flask import Flask, request, jsonify
from sentry_sdk.integrations.flask import FlaskIntegration

from PIL import Image
import requests
from torchvision import transforms
from transformers import BlipProcessor, BlipForConditionalGeneration

sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    if torch.cuda.is_available():
        logger.info("fromage is set to run on cuda")
        processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-large")
        logger.info("fromage processor created")
        model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-large").to("cuda")
        logger.info("fromage model imported")
    logger.info("fromage is ready")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e

app = Flask(__name__)
logging.getLogger("werkzeug").setLevel("WARNING")

def generate_responses(image_path, prompt):
    image = Image.open(requests.get(image_path, stream=True).raw).convert('RGB')
    logger.info("Image transformed")  
    text = "a photography of"
    inputs = processor(image, text, return_tensors="pt").to("cuda")
    out = model.generate(**inputs)
    model_answer = processor.decode(out[0], skip_special_tokens=True)
    logger.info([model_answer])
    return [model_answer]


@app.route("/respond", methods=["POST"])
def respond():
    st_time = time.time()
    image_paths = request.json.get("image_paths")
    sentences = request.json.get("sentences")

    # frmg_answers = []
    for image_path, sentence in zip(image_paths, sentences):
        if image_path and image_path.lower().endswith(('.png', '.jpg', '.jpeg')):
            try:
                frmg_answers = generate_responses(image_path, sentence)
            except Exception as exc:
                logger.exception(exc)
                sentry_sdk.capture_exception(exc)
                frmg_answers = [""]
        else:
            frmg_answers = [""]

    total_time = time.time() - st_time
    logger.info(f"fromage results: {frmg_answers}")
    logger.info(f"fromage exec time: {total_time:.3f}s")
    logger.info(jsonify(frmg_answers))
    return jsonify(frmg_answers)
