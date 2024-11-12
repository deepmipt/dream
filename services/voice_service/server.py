import logging
import os
import time
import json
import sys
import re
from itertools import zip_longest
import asyncio
import subprocess

sys.path.append("/src/")
sys.path.append("/src/AudioCaption/")
sys.path.append("/src/AudioCaption/captioning/")
sys.path.append("/src/AudioCaption/captioning/pytorch_runners/")

import sentry_sdk
from AudioCaption.captioning.pytorch_runners.inference_waveform import inference
from urllib.request import urlretrieve

from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware
from typing import List


CAP_ERR_MSG = "The audiofile format is not supported"
AUDIO_DIR = "/src/audio_input/"
MODEL_PATH = "/src/AudioCaption/clotho_cntrstv_cnn14rnn_trm/swa.pth"

sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))

SERVICE_PORT = int(os.getenv("SERVICE_PORT"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

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
    sound_paths: List[str] = []
    sound_durations: List[int] = []
    sound_types: List[str] = []
    video_paths: List[str] = []
    video_durations: List[int] = []
    video_types: List[str] = []


async def subinfer(paths, durations, types):
    write_task_state({"state": "scheduled"})    
    responses = []

    for path, duration, atype in zip_longest(paths, durations, types):
        logger.info(f"Processing batch at sound_annotator: {path}, {duration}, {atype}")
        filename_els = path.split("=")
        filename = filename_els[-1]
        filename = re.sub(r"^[^\w\d.]+|[^\w\d.]+$", "",filename)
        filetype = filename.split(".")[-1]
        filetype = re.sub(r"^[^\w\d]+|[^\w\d]+$", "",filetype)
        logger.info(filetype)

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
                if i.split(".")[-1] == "wav":
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
            responses += [{"sound_type": atype, "sound_duration": duration, "sound_path": path, "caption": caption}]
        except Exception as e:
            logger.info(f"An error occurred in voice-service: {CAP_ERR_MSG}, {e}")
            responses.append(
                [{"sound_type": atype, "sound_duration": duration, "sound_path": path, "caption": "Error"}]
            )
            
    write_task_state({"task_state": "done", "response": responses})
    logger.info(f"VOICE_SERVICE RESPONSE: {responses}")
    

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/respond")
async def infer(payload: VoicePayload):
    st_time = time.time()
    responses = []
    task_state = read_task_state()
    logger.info(f"Task state: {task_state}")
    
    if not task_state.get("task_state") and (payload.sound_paths or payload.video_paths):
        print('Async process start')
        asyncio.create_task(subinfer(payload.sound_paths, payload.sound_durations, payload.sound_types))
        responses.append({"task_state": "task_scheduled"})
        
    if task_state.get("task_state") == "scheduled":
        responses.append(task_state)
    elif task_state.get("task_state") == "done":
        responses.append(task_state)
        write_task_state({"task_state": ""})

    total_time = time.time() - st_time
    logger.info(f"voice_service exec time: {total_time:.3f}s")
    return jsonable_encoder(responses)