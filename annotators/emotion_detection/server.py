import logging
import os
import json
import time
import uuid

import opensmile
import torch
import numpy as np
import sentry_sdk
import cv2
import aux  # noqa: F401

from multimodal_concat.models import MultimodalClassificationModel, MainModel
from multimodal_concat.utils import prepare_models

from fastapi import FastAPI, BackgroundTasks
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware
from transformers import AutoTokenizer, AutoProcessor
from typing import List, Optional
from urllib.request import urlretrieve


sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))

label2id = {
    "anger": 0,
    "disgust": 1,
    "fear": 2,
    "joy": 3,
    "neutral": 4,
    "sadness": 5,
    "surprise": 6,
}
id2label = {v: k for k, v in label2id.items()}
num_labels = 7
text_model, video_model, audio_model = prepare_models(num_labels, os.getenv("MODEL_PATH"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

text_model_name = os.getenv("TEXT_PRETRAINED")
tokenizer = AutoTokenizer.from_pretrained(text_model_name)

video_model_name = os.getenv("VIDEO_PRETRAINED")
video_feature_extractor = AutoProcessor.from_pretrained(video_model_name)

smile = opensmile.Smile(
    opensmile.FeatureSet.ComParE_2016,
    opensmile.FeatureLevel.Functionals,
    sampling_rate=16000,
    resample=True,
    num_workers=5,
    verbose=True,
)

redundant_features = os.getenv("REDUNDANT_FEATURES")
with open(redundant_features, "r") as features_file:
    redundant_features_list = features_file.read().split(",")
    
TASKS_DIR = "tasks"

os.makedirs(TASKS_DIR, exist_ok=True)


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


def sample_frame_indices(seg_len, clip_len=16, frame_sample_rate=4):
    converted_len = int(clip_len * frame_sample_rate)
    converted_len = min(converted_len, seg_len - 1)
    end_idx = np.random.randint(converted_len, seg_len)
    start_idx = end_idx - converted_len
    indices = np.linspace(start_idx, end_idx, num=clip_len)
    indices = np.clip(indices, start_idx, end_idx - 1).astype(np.int64)
    return indices


def _video_capturing(file_path):
    cap = cv2.VideoCapture(file_path)
    v_len = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    indices = sample_frame_indices(v_len)

    for fn in range(v_len):
        success, frame = cap.read()
        if success is False:
            continue
        if fn in indices:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            res = cv2.resize(frame, dsize=(224, 224), interpolation=cv2.INTER_CUBIC)
            yield res
            
    cap.release()
    

def get_frames(
    file_path,
    clip_len=16,
):
    frames = [e for e in _video_capturing(file_path)]

    if len(frames) < clip_len:
        add_num = clip_len - len(frames)
        frames_to_add = [frames[-1] for _ in range(add_num)]
        frames.extend(frames_to_add)

    return frames


def create_final_model():
    multi_model = MultimodalClassificationModel(
        text_model,
        video_model,
        audio_model,
        num_labels,
        input_size=4885,
        hidden_size=512,
    )
    checkpoint = torch.load(os.getenv("MULTIMODAL_MODEL"))
    multi_model.load_state_dict(checkpoint)

    device = "cuda"
    return MainModel(multi_model, device=device)


def process_text(input_tokens: str):
    return tokenizer(
        input_tokens,
        padding="max_length",
        truncation=True,
        max_length=128,
        return_tensors="pt",
    )


def process_video(video_path: str):
    video_frames = get_frames(video_path)
    video_frames = np.array(video_feature_extractor(videos=video_frames).pixel_values)
    video_frames = torch.tensor(video_frames)
    return {'pixel_values': video_frames}


def process_audio(file_path: str):
    audio_features = smile.process_files([file_path])
    audio_features = audio_features.drop(columns=redundant_features_list, inplace=False)
    return audio_features.values.reshape(audio_features.shape[0], 1, audio_features.shape[1])


def inference(text: str, video_path: str):
    text_encoding = process_text(text).to("cuda")
    video_encoding = process_video(video_path)
    video_encoding["pixel_values"] = video_encoding["pixel_values"].to("cuda")
    audio_features = process_audio(video_path)
    audio_features = torch.tensor(audio_features).to("cuda")
    batch = {
        "text": text_encoding,
        "video": video_encoding,
        "audio": audio_features,
        "label": None,
    }
    label = final_model(batch)
    return id2label[int(label.detach().cpu())]


def predict_emotion(text: str, video_path: str):
    try:
        result = inference(text, video_path)
        logger.warning(f"{result}")
        return result
    except Exception as e:
        sentry_sdk.capture_exception(e)
        raise e


final_model = create_final_model()


class EmotionsPayload(BaseModel):
    text: List[str]
    video_path: List[str]
    task_id: Optional[list] = None
        
        
class TaskStatus(BaseModel):
    task_id: str
    status: str
    result: Optional[list] = None


def subinfer(task_id: str, msg_text: str, video_path: str):
    write_task_status(task_id, "pending")
    
    try:
        if not os.path.exists(video_path):
            filename = video_path.split("=")[-1]
            filepath = f"/data/{filename}"
            urlretrieve(video_path, filepath)
        else:
            filepath = video_path
        logger.info(f"File path: {filepath}")
        if not os.path.exists(filepath):
            write_task_status(task_id, "failed")
            raise ValueError(f"Failed to retrieve videofile from {filepath}")
        emotion = predict_emotion(f'{msg_text} ', filepath)
        logger.info("LONG TASK DONE")
        write_task_state({"task_state": "done", "emotion": emotion})
    except Exception as e:
        write_task_status(task_id, "failed")
        raise ValueError(f"The message format is correct, but: {e}")

    write_task_status(task_id, "completed", [emotion])


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/model", response_model=TaskStatus)
def infer(payload: EmotionsPayload, background_tasks: BackgroundTasks):
    st_time = time.time()
    logger.info(f"Emotion Detection: {payload}")
    
    if not payload.task_id:
        task_id = str(uuid.uuid4())
        write_task_status(task_id, "pending")
        if payload.text or payload.video_path:
            for text, path in zip(payload.text, payload.video_path):
                background_tasks.add_task(subinfer, task_id, text, path)
    else:
        task_id = payload.task_id[0]

    total_time = time.time() - st_time
    logger.info(f"task_scheduler exec time: {total_time:.3f}s")

    task_file = read_task_status(task_id)
    logger.info(f"Task file: {task_file}")
    task_file = TaskStatus(**task_file)
    
    return task_file
