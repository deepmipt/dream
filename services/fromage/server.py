import logging
import os
import time
import torch
import sentry_sdk
import json
import uuid
import sys

from PIL import Image
import requests
from transformers import BlipProcessor, BlipForConditionalGeneration
from itertools import zip_longest

from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware
from typing import List

sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


try:
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logger.info(device)
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

TASKS_DIR = "/src/aux_files/tasks"
os.makedirs(TASKS_DIR, exist_ok=True)


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)   


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

def read_task_status(task_id):
    task_file = os.path.join(TASKS_DIR, f"{task_id}.json")
    if os.path.exists(task_file):
        with open(task_file, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return None

def write_task_status(task_id, status, result=None):
    task_file = os.path.join(TASKS_DIR, f"{task_id}.json")
    task_status = {
        "task_id": task_id,
        "status": status,
        "result": result
    }
    with open(task_file, "w", encoding="utf-8") as f:
        json.dump(task_status, f)

def subinfer(task_id: str, image_paths: list, sentences: list):
    write_task_status(task_id, "pending")
    responses = []
    for image_path, sentence in zip_longest(image_paths, sentences):
        if image_path and image_path.lower().endswith(('.png', '.jpg', '.jpeg')):
            try:
                frmg_answers = generate_responses(image_path, sentence)
                responses.append({"image_path": image_path, "caption": frmg_answers[0]})
            except Exception as exc:
                logger.exception(exc)
                sentry_sdk.capture_exception(exc)
                responses.append({"image_path": image_path, "caption": "Error"})
        else:
            responses.append({"image_path": image_path, "caption": "Invalid image"})
    write_task_status(task_id, "completed", responses)
    logger.info(f"fromage RESPONSE: {responses}")         


@app.post("/respond")
def respond(payload: FromagePayload, background_tasks: BackgroundTasks):
    st_time = time.time()
    task_id = str(uuid.uuid4())
    write_task_status(task_id, "pending")
    background_tasks.add_task(subinfer, task_id, payload.image_paths, payload.sentences)

    all_tasks = []
    for filename in os.listdir(TASKS_DIR):
        if filename.endswith(".json"):
            task_file_path = os.path.join(TASKS_DIR, filename)
            try:
                with open(task_file_path, "r") as file:
                    task_data = json.load(file)
                    task_info = {
                        "task_id": task_data.get("task_id"),
                        "status": task_data.get("status"),
                        "result": task_data.get("result")
                    }
                    all_tasks.append(task_info)
            except json.JSONDecodeError:
                logger.error(f"Error decoding JSON in file: {task_file_path}")
            except Exception as e:
                logger.error(f"An error occurred while processing file {task_file_path}: {e}")

    total_time = time.time() - st_time
    cur_status_json = [
        {
            "id": task["task_id"],
            "status": task["status"],
            "caption": task["result"] or "N/A"
        }
        for task in all_tasks] 
    result = {
        "task_id": task_id,
        "status": "pending",
        "all_status": cur_status_json
    }
    logger.info(f"fromage exec time: {total_time:.3f}s")
    return result
