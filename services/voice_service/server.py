import logging
import os
import time
import json
import sys
import re
from itertools import zip_longest
import uuid
import subprocess

sys.path.append("/src/")
sys.path.append("/src/AudioCaption/")
sys.path.append("/src/AudioCaption/captioning/")
sys.path.append("/src/AudioCaption/captioning/pytorch_runners/")

import sentry_sdk
from AudioCaption.captioning.pytorch_runners.inference_waveform import inference
from urllib.request import urlretrieve

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware
from typing import List, Optional


CAP_ERR_MSG = "The audiofile format is not supported"
AUDIO_DIR = "/src/audio_input/"
MODEL_PATH = "/src/AudioCaption/clotho_cntrstv_cnn14rnn_trm/swa.pth"

sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))

SERVICE_PORT = int(os.getenv("SERVICE_PORT"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

logging.getLogger("werkzeug").setLevel("WARNING")

TASKS_DIR = "tasks"

os.makedirs(TASKS_DIR, exist_ok=True)


result = subprocess.run(
    ["curl", "-F", "file=@audio_input/rain.wav", "files:3000"],
    capture_output=True, text=True
)

result = subprocess.run(
    ["curl", "-F", "file=@audio_input/rain.mp3", "files:3000"],
    capture_output=True, text=True
)

# Importing mp3's for testing
result = subprocess.run(
    ["curl", "-F", "file=@audio_input/01-BikeDemo_Speaker.mp3", "files:3000"],
    capture_output=True, text=True
)
result = subprocess.run(
    ["curl", "-F", "file=@audio_input/00_BRUSH.mp3", "files:3000"],
    capture_output=True, text=True
)
result = subprocess.run(
    ["curl", "-F", "file=@audio_input/002_78_rpm_vinyl_noise_44_16_lossless.mp3", "files:3000"],
    capture_output=True, text=True
)
result = subprocess.run(
    ["curl", "-F", "file=@audio_input/00264%20hill%20creek 1.mp3", "files:3000"],
    capture_output=True, text=True
)
result = subprocess.run(
    ["curl", "-F", "file=@audio_input/department.store.mp3", "files:3000"],
    capture_output=True, text=True
)
result = subprocess.run(
    ["curl", "-F", "file=@audio_input/mosquito.mp3", "files:3000"],
    capture_output=True, text=True
)
result = subprocess.run(
    ["curl", "-F", "file=@audio_input/smeared%20bell.mp3", "files:3000"],
    capture_output=True, text=True
)
result = subprocess.run(
    ["curl", "-F", "file=@audio_input/street_corner.mp3", "files:3000"],
    capture_output=True, text=True
)
result = subprocess.run(
    ["curl", "-F", "file=@audio_input/Water%20Sound.mp3", "files:3000"],
    capture_output=True, text=True
)
result = subprocess.run(
    ["curl", "-F", "file=@audio_input/Whining%20Dog.mp3", "files:3000"],
    capture_output=True, text=True
)


class VoicePayload(BaseModel):
    sound_paths: List[Optional[str]] = []
    sound_durations: List[Optional[int]] = []
    sound_types: List[Optional[str]] = []
    video_paths: List[Optional[str]] = []
    video_durations: List[Optional[int]] = []
    video_types: List[Optional[str]] = []
        

class TaskStatus(BaseModel):
    task_id: str
    status: str
    result: Optional[str] = None


def subinfer(task_id: str, 
             paths: list, 
             durations: list, 
             types: list):
    responses = []

    for path, duration, atype in zip_longest(paths, durations, types):
        logger.info(f"Processing batch at sound_annotator: {path}, {duration}, {atype}")
        filename_els = path.split("=")
        filename = filename_els[-1]
        filename = re.sub(r"^[^\w\d.]+|[^\w\d.]+$", "",filename)
        filetype = filename.split(".")[-1]
        filetype = re.sub(r"^[^\w\d]+|[^\w\d]+$", "",filetype)

        if not os.path.exists(AUDIO_DIR):
            os.makedirs(AUDIO_DIR)

        for i in os.listdir(AUDIO_DIR):
            os.remove(os.path.join(AUDIO_DIR, i))
        try:
            urlretrieve(path, os.path.join(AUDIO_DIR, filename))
            logger.info(f"Файл сохранен в {os.path.join(AUDIO_DIR, filename)}")
        except Exception as e:
            logger.error(f"Ошибка при загрузке файла: {e}")
        try:
            if filetype in ["oga", "mp3", "MP3", "ogg", "flac", "mp4"]:

                logger.info(f"ffmpegging .{filetype} to .wav")

                process = subprocess.run(
                    [
                        "ffmpeg",
                        "-i",
                        os.path.join(AUDIO_DIR, filename),
                        os.path.join(AUDIO_DIR, filename[: -len(filetype)] + "wav"),
                    ]
                )

                logger.info("ffmpegging finished successfully")
                if process.returncode != 0:
                    raise Exception("Something went wrong")
        except Exception as e:
            logger.info(f"An error occurred in ffmpeging {e}")
        try:
            logger.info(f"Scanning AUDIO_DIR ({AUDIO_DIR}) for wav files...")
            fname = "NOFILE"
            for i in os.listdir(AUDIO_DIR):
                logger.info(f"{filename.split('.')[0]}, {str(i.split('.')[0])}")
                if (i.split(".")[0] == filename.split(".")[0]) and (i.split(".")[-1] == "wav"):
                    logger.info(f"found file: {os.path.join(AUDIO_DIR, i)}")
                    inference(os.path.join(AUDIO_DIR, i), "/src/output.json", MODEL_PATH)
                    fname = i
                    break
            else:
                CAP_ERR_MSG = "No files for inference found in AUDIO_DIR"
                raise Exception(CAP_ERR_MSG)
            logger.info("Inference finished successfully")
            with open('/src/output.json', 'r') as file:
                caption = json.load(file)[fname]
            responses += [{"sound_type": atype, "sound_duration": duration, "sound_path": path, "caption": caption}] # FIXME
        except Exception as e:
            logger.info(f"An error occurred in voice-service: {CAP_ERR_MSG}, {e}")
            responses +=[{"sound_type": atype, "sound_duration": duration, "sound_path": path, "caption": "Error"}]

    logger.info(f"VOICE_SERVICE RESPONSE: {responses}")
    task_file = os.path.join(TASKS_DIR, f"{task_id}.json")
    with open(task_file, "w", encoding="utf-8") as f:
        status = "failed" if responses[0]["caption"] == "Error" else "completed"
        task_status = {
                "task_id": task_id,
                "status": status,
                "result": responses
            }
        json.dump(task_status, f)
    

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/respond")
def infer(payload: VoicePayload, background_tasks: BackgroundTasks):
    st_time = time.time()
    logger.info(f'payload: {payload}')
    bad_filenames_present = any([
        'non_existent' in el for el in payload.sound_paths])
    if not bad_filenames_present:
        task_id = str(uuid.uuid4())
        task_initial = {
            "task_id": task_id,
            "status": "pending",
            "result": None
        }
        task_file = os.path.join(TASKS_DIR, f"{task_id}.json")
        with open(task_file, "w", encoding="utf-8") as f:
            json.dump(task_initial, f)
        background_tasks.add_task(subinfer, 
                                task_id, 
                                payload.sound_paths, 
                                payload.sound_durations, 
                                payload.sound_types)
    else:
        task_id = "non_existent_task"
    total_time = time.time() - st_time

    all_tasks = []

    for filename in os.listdir(TASKS_DIR):
        if filename.endswith(".json"):
            task_file_path = os.path.join(TASKS_DIR, filename)
            
            try:
                with open(task_file_path, "r") as file:
                    task_data = json.load(file)
                    
                    t_id = task_data.get("task_id")
                    status = task_data.get("status")
                    result = str(task_data.get("result")) if task_data.get("result") is not None else None
                    
                    task_info = {
                        "task_id": t_id,
                        "status": status,
                        "result": result
                    }
                    
                    all_tasks.append(task_info)
            
            except json.JSONDecodeError:
                print(f"Error decoding JSON in file: {task_file_path}")
            except Exception as e:
                print(f"An error occurred while processing file {task_file_path}: {e}")

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
    # result_json = json.dumps(result)
    # logger.info(result_json)

    logger.info(f"voice_service exec time: {total_time:.3f}s")

    return result