import logging
import os
import time
import torch
import sentry_sdk
import asyncio
import json

from PIL import Image
import requests
from torchvision import transforms
from transformers import BlipProcessor, BlipForConditionalGeneration

from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware
from typing import List

sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))

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

logging.getLogger("werkzeug").setLevel("WARNING")

STATE_FILE = "task_state.json"


def read_task_state():
    try:
        with open(STATE_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {"task_state": ""}

    
def write_task_state(state):
    with open(STATE_FILE, "w") as file:
        json.dump(state, file)


class FromagePayload(BaseModel):
    image_paths: List[str] = []
    sentences: List[str] = []


def generate_responses(image_path, prompt):
    image = Image.open(requests.get(image_path, stream=True).raw).convert('RGB')
    logger.info("Image transformed")  
    text = "a photography of"
    inputs = processor(image, text, return_tensors="pt").to("cuda")
    out = model.generate(**inputs)
    model_answer = processor.decode(out[0], skip_special_tokens=True)
    logger.info([model_answer])
    return [model_answer]


async def subinfer(image_paths, sentences):
    write_task_state({"task_state": "scheduled"})
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
    write_task_state({"task_state": "done", "response": frmg_answers})
    logger.info(f"VOICE_SERVICE RESPONSE: {frmg_answers}")

            
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)            
            

@app.post("/respond")
async def respond(payload: FromagePayload):
    st_time = time.time()
    responses = []
    task_state = read_task_state()
    logger.info(f"Task state: {task_state}")
    
    if not task_state.get("task_state") and payload.image_paths:
        asyncio.create_task(subinfer(payload.image_paths, payload.sentences))
        responses.append({"task_state": "scheduled"})
        
    if task_state.get("task_state") == "scheduled":
        responses.append(task_state)
    elif task_state.get("task_state") == "done":
        responses.append(task_state)
        write_task_state({"task_state": ""})

    total_time = time.time() - st_time
    logger.info(f"fromage exec time: {total_time:.3f}s")
    return jsonable_encoder(responses)