import logging
import os
import time
from itertools import zip_longest
import asyncio
import json

import sentry_sdk
from urllib.request import URLopener
from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware
from typing import List

import whisper
import whisperx
import pickle

import subprocess


import sys
sys.path.append('/src/aux_files/VidChapters')
from args import MODEL_DIR


CAP_ERR_MSG = "The file format is not supported"
CHECKPOINTS = "/src/aux_files/checkpoint_vidchapters"
MODEL_PATH = "/src/aux_files/captioning_model.pth"
DATA_DIR = "/src/aux_files/data/video_captioning"
ASR_MODEL = "/src/aux_files/TOFILL/large-v2.pt"
DEVICE='cpu'

sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# create asr whisper model here

asr_model = whisper.load_model('/src/aux_files/large-v2.pt', device='cpu', download_root='/src/aux_files/TOFILL')

logging.getLogger("werkzeug").setLevel("WARNING")

STATE_FILE = "task_state.json"


def read_task_state():
    try:
        with open(STATE_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {"state": ""}

    
def write_task_state(state):
    with open(STATE_FILE, "w") as file:
        json.dump(state, file)


class VideoPayload(BaseModel):
    video_paths: List[str] = []
    video_durations: List[int] = []
    video_types: List[str] = []


def generate_asr(video_path, asr_output_path):
    logger.info("ASR captioning")
    try:
        asr = asr_model.transcribe(video_path)
        # logger.info("ASR.model")
        align_model, metadata = whisperx.load_align_model(language_code='en', device = DEVICE, model_dir=os.path.join('/src/aux_files', MODEL_DIR))
        audio = whisperx.load_audio(video_path)
        # logger.info("Whisperx.load_audio", audio)
        aligned_asr = whisperx.align(asr["segments"], align_model, metadata, audio, DEVICE, return_char_alignments=False)
        # logger.info("Aligned", aligned_asr)
        pickle.dump(aligned_asr, open(asr_output_path, 'wb'))
    except Exception as e:
        logger.warning(f"str{e}, {type(e)=}")
    
    return asr_output_path


def gen_video_caption(video_path, asr_caption):
    # takes 1 min
    path_2_demo = '/src/aux_files/VidChapters/demo_vid2seq.py'
    command = [
        "python", 
        path_2_demo,
        f'--load={MODEL_PATH}',
        f'--video_example={video_path}',
        f'--asr_example={asr_caption}',
        "--combine_datasets", "chapters",
        "--device", "cpu"
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True)
        # logger.info(result.stdout)
    except Exception as e:
        logger.warning(f"str{e}, {type(e)=}")
    return result.stdout


def get_answer(video_path, asr_output_path):
    asr_caption = generate_asr(video_path, asr_output_path)
    logger.info("ASR caption is ready. Video chapters in processing.")
    video_caption = gen_video_caption(video_path, asr_caption)
    logger.info("Inference finished successfully")
    return video_caption


async def subinfer(paths, durations, types):
    write_task_state({"state": "scheduled"})
    responses = []
    
    for path, duration, atype in zip_longest(paths, durations, types):
        logger.info(f"Processing batch at vidchapters annotator: {path}")
        if '=' in path:
            filename_els = path.split("=")
        else:
            filename_els = path.split('/')
        filename = filename_els[-1]

        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)

        for i in os.listdir(DATA_DIR):
            os.remove(os.path.join(DATA_DIR, i))

        if filename.split(".")[-1] in ["oga", "ogg", "mp4", "webm"]:
            file = URLopener()
            file.retrieve(path, os.path.join(DATA_DIR, filename))
        try:
            logger.info(f"Scanning DATA_DIR ({DATA_DIR}) for files...")
            for i in os.listdir(DATA_DIR):
                # i is a filename without path
                logger.info("Scanning finished successfully, files found, starting inference...")
                break
            else:
                CAP_ERR_MSG = "No files for inference found in DATA_DIR"
                raise Exception(CAP_ERR_MSG)
            
            asr_output_path = os.path.join(DATA_DIR, i.split(".")[0]+'_asr')
            video_path = os.path.join(DATA_DIR, i)
            video_caption = get_answer(video_path, asr_output_path)
            responses.append({"video_captioning_chapters": video_caption})
        except Exception:
            logger.info(f"An error occurred in vidchapters-service: {CAP_ERR_MSG}")
            responses.append(
                [{"video_captioning_chapters": "Error occured"}]
            )

    logger.info(f"VIDCHAPTERS_SERVICE RESPONSE: {responses}")
    write_task_state({"state": "done", "response": responses})
        

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/respond")
async def respond(payload: VideoPayload):
    st_time = time.time()
    task_state = read_task_state()
    logger.info(f"Task state: {task_state}")
    logger.info(f'Paths: {payload.video_paths}')

    responses = []
    
    if not task_state.get("state") and payload.video_paths:
        asyncio.create_task(subinfer(payload.video_paths, payload.video_durations, payload.video_types))
        responses.append({"state": "scheduled"})
                
    if task_state.get("state") == "scheduled":
        responses.append(task_state)
    elif task_state.get("state") == "done":
        responses.append(task_state)
        write_task_state({"state": ""})

    total_time = time.time() - st_time
    logger.info(f"service exec time: {total_time:.3f}s")
    return jsonable_encoder(responses)
