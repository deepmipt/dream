import logging
import os
import opensmile
from multimodal_concat.models import MultimodalClassificaionModel, MainModel
from multimodal_concat.utils import prepare_models

import torch
import numpy as np
import sentry_sdk
from flask import Flask, jsonify, request
from sentry_sdk.integrations.flask import FlaskIntegration
from transformers import AutoTokenizer, AutoProcessor
import cv2

sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])
app = Flask(__name__)

label2id = {'anger': 0, 'disgust': 1, 'fear': 2, 'joy': 3, 'neutral': 4, 'sadness': 5, 'surprise': 6}
num_labels = 7
text_model, video_model, audio_model = prepare_models(num_labels, "./")

logger = logging.getLogger(__name__)


def sample_frame_indices(seg_len, clip_len=16, frame_sample_rate=4, mode="video"):
    converted_len = int(clip_len * frame_sample_rate)
    converted_len = min(converted_len, seg_len-1)
    end_idx = np.random.randint(converted_len, seg_len)
    start_idx = end_idx - converted_len
    if mode == "video":
        indices = np.linspace(start_idx, end_idx, num=clip_len)
    else:
        indices = np.linspace(start_idx, end_idx, num=clip_len*frame_sample_rate)
    indices = np.clip(indices, start_idx, end_idx - 1).astype(np.int64)
    return indices


def get_frames(file_path, clip_len=16,):
    cap = cv2.VideoCapture(file_path)
    v_len = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    indices = sample_frame_indices(v_len)

    frames = []
    for fn in range(v_len):
        success, frame = cap.read()
        if success is False:
            continue
        if (fn in indices):
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  
            res = cv2.resize(frame, dsize=(224, 224), interpolation=cv2.INTER_CUBIC)
            frames.append(res)
    cap.release()

    if len(frames) < clip_len:
        add_num = clip_len - len(frames)
        frames_to_add = [frames[-1]] * add_num
        frames.extend(frames_to_add)

    return frames

def create_final_model():
    multi_model = MultimodalClassificaionModel(
        text_model,
        video_model,
        audio_model,
        num_labels,
        input_size=1920, 
        hidden_size=512
    )
    checkpoint = torch.load('final_model.pt')
    multi_model.load_state_dict(checkpoint)

    device = 'cuda'
    return MainModel(multi_model, device=device)


def process_text(input_tokens: str):
    text_model_name = 'bert-large-uncased'
    tokenizer = AutoTokenizer.from_pretrained(text_model_name)

    return tokenizer(input_tokens,
                    padding='max_length',
                    truncation=True,
                    max_length=128,
                    return_tensors='pt')


def process_video(video_path: str):
    video_frames = get_frames(video_path)

    video_model_name = "microsoft/xclip-base-patch32"
    video_feature_extractor = AutoProcessor.from_pretrained(video_model_name)

    return video_feature_extractor(videos=video_frames, return_tensors="pt")


def process_audio(file_path: str):
    smile = opensmile.Smile(
        opensmile.FeatureSet.ComParE_2016,
        opensmile.FeatureLevel.Functionals,
        sampling_rate=16000,    
        resample=True,    
        num_workers=5,
        verbose=True,
    )

    audio_features = smile.process_files([file_path])
    return audio_features.values.reshape(audio_features.shape[0], 1, audio_features.shape[1])


def infer(text: str, video_path: str):
    text_encoding = process_text(text)
    video_encoding = process_video(video_path)
    audio_features = process_audio(video_path)
    batch = {'text': text_encoding, 'video': video_encoding, 'audio': audio_features, 'label': None}
    label = final_model(batch)
    id2label = {v: k for k, v in label2id.items()}
    return id2label[int(label.detach().cpu())]


def predict_emotion(text: str, video_path: str):
    try:
        return infer(text, video_path)
    except Exception as e:
        sentry_sdk.capture_exception(e)
        raise e


final_model = create_final_model()


@app.route("/model", methods=["POST"])
def infer():
    msg_text = request.json["last_human_utterances"][-1]["text"]
    msg_split = msg_text.split('\n')

    if all([len(msg_split) == 2, "https://" in msg_split[1], len(msg_split[0])]):
        try:
            logger.info(f"Emotion Detection: {msg_text}")
            emotion = predict_emotion(msg_split[0], msg_split[1])
        except Exception as e:
            raise ValueError(f"The message format is correct, but: {e}")
    else:
        raise ValueError("Input should be text and a videofile link on two separate lines.")
    return jsonify(emotion)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8027)