import logging
import os
import time
from itertools import zip_longest
import json
import uuid

import sentry_sdk
from urllib.request import URLopener
from fastapi import FastAPI, BackgroundTasks
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
DEVICE = 'cpu'

sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Create ASR Whisper model here
asr_model = whisper.load_model(
    '/src/aux_files/large-v2.pt', device='cpu', download_root='/src/aux_files/TOFILL'
)

logging.getLogger("werkzeug").setLevel("WARNING")

TASKS_DIR = "tasks"
os.makedirs(TASKS_DIR, exist_ok=True)


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class VideoPayload(BaseModel):
    video_paths: List[str] = []
    video_durations: List[int] = []
    video_types: List[str] = []


def generate_asr(video_path, asr_output_path):
    logger.info("ASR captioning")
    try:
        asr = asr_model.transcribe(video_path)
        align_model, metadata = whisperx.load_align_model(
            language_code='en', device=DEVICE, model_dir=os.path.join('/src/aux_files', MODEL_DIR)
        )
        audio = whisperx.load_audio(video_path)
        aligned_asr = whisperx.align(
            asr["segments"],
            align_model,
            metadata,
            audio,
            DEVICE,
            return_char_alignments=False,
        )
        pickle.dump(aligned_asr, open(asr_output_path, 'wb'))
    except Exception as e:
        logger.warning(f"str{e}, {type(e)=}")

    return asr_output_path


def gen_video_caption(video_path, asr_caption):
    path_2_demo = '/src/aux_files/VidChapters/demo_vid2seq.py'
    command = [
        "python",
        path_2_demo,
        f'--load={MODEL_PATH}',
        f'--video_example={video_path}',
        f'--asr_example={asr_caption}',
        "--combine_datasets",
        "chapters",
        "--device",
        "cpu",
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True)
    except Exception as e:
        logger.warning(f"str{e}, {type(e)=}")
        result = None
    return result.stdout if result else "Error"


def get_answer(video_path, asr_output_path):
    asr_caption = generate_asr(video_path, asr_output_path)
    logger.info("ASR caption is ready. Video chapters in processing.")
    video_caption = gen_video_caption(video_path, asr_caption)
    logger.info("Inference finished successfully")
    return video_caption


def write_task_status(task_id, status, result=None):
    task_file = os.path.join(TASKS_DIR, f"{task_id}.json")
    task_status = {
        "task_id": task_id,
        "status": status,
        "result": result,
    }
    with open(task_file, "w", encoding="utf-8") as f:
        json.dump(task_status, f)


def read_task_status(task_id):
    task_file = os.path.join(TASKS_DIR, f"{task_id}.json")
    if os.path.exists(task_file):
        with open(task_file, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return None


def subinfer(task_id, paths, durations, types):
    write_task_status(task_id, "pending")
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
                if (i.split(".")[0] == filename.split(".")[0]):
                    asr_output_path = os.path.join(DATA_DIR, i.split(".")[0] + '_asr')
                    video_path = os.path.join(DATA_DIR, i)                    
                    logger.info("Scanning finished successfully, files found, starting inference...")
                    video_caption = get_answer(video_path, asr_output_path)
                    break
            else:
                cap_err_msg = "No files for inference found in DATA_DIR"
                raise Exception(cap_err_msg)
            
            responses += [{"video_type": atype, "video_duration": duration, "video_path": path, "caption": video_caption}]
        except Exception as e:
            logger.info(f"An error occurred in vidchapters-service: {CAP_ERR_MSG}, {e}")
            responses += [{"video_type": atype, "video_duration": duration, "video_path": path, "caption": "Error occurred"}]

    logger.info(f"VIDCHAPTERS_SERVICE RESPONSE: {responses}")
    status = (
        "failed" if any(resp.get("caption") == "Error occurred" for resp in responses) else "completed"
    )
    write_task_status(task_id, status, responses)


@app.post("/respond")
def respond(payload: VideoPayload, background_tasks: BackgroundTasks):
    st_time = time.time()
    bad_filenames_present = any([
        'non_existent' in el for el in payload.video_paths])
    if not bad_filenames_present:
        task_id = str(uuid.uuid4())
        write_task_status(task_id, "pending")
        background_tasks.add_task(
            subinfer, task_id, payload.video_paths, payload.video_durations, payload.video_types
        )
    else:
        task_id = "non_existent_task"
    total_time = time.time() - st_time

    all_tasks = []
    for filename in os.listdir(TASKS_DIR):
        if filename.endswith(".json"):
            task_file_path = os.path.join(TASKS_DIR, filename)
            try:
                with open(task_file_path, "r") as f:
                    task_data = json.load(f)
                    task_info = {
                        "task_id": task_data.get("task_id"),
                        "status": task_data.get("status"),
                        "result": task_data.get("result"),
                    }
                    all_tasks.append(task_info)
            except json.JSONDecodeError:
                logger.error(f"Error decoding JSON in file: {task_file_path}")
            except Exception as e:
                logger.error(f"An error occurred while processing file {task_file_path}: {e}")

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

    logger.info(f"service exec time: {total_time:.3f}s")
    
    return result
