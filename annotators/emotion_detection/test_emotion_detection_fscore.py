import aux

from multimodal_concat.custom_datasets import MultimodalDataset
from multimodal_concat.models import MultimodalClassificationModel, MainModel
from multimodal_concat.utils import prepare_models, test, add_utt_numeration

import os
import random
import numpy as np
import pandas as pd

import torch
from torch.utils.data import DataLoader
from transformers import AutoTokenizer, AutoProcessor


def fix_minor_mistakes():
    path = "/test/meld_testdata/Video/dia0_utt0/cutFrames"
    for f in os.listdir(path):
        newf = f'old{f}'
        os.rename(f'{path}/{f}', f'{path}/{newf}')
    for i, f in enumerate(os.listdir(path)):
        newf = f'{i+1}.png'
        os.rename(f'{path}/{f}', f'{path}/{newf}')

def create_video_df(text_df: pd.DataFrame):
    fp = [f'dia{dianum}_utt{uttnum}/cutFrames' for dianum, uttnum in zip(text_df['dialog num'].values,
                              text_df['utt num'].values)]
    text_df['file_path'] = fp
    return text_df
    

def prepare_testdataloader(bs, text_path, audio_path, video_path, label2id):
    test_text = add_utt_numeration(pd.read_csv(text_path))
    test_video = create_video_df(test_text)
    test_audio = pd.read_csv(audio_path)
    
    text_model_name = os.getenv("TEXT_PRETRAINED")
    tokenizer = AutoTokenizer.from_pretrained(text_model_name)
    video_model_name = os.getenv("VIDEO_PRETRAINED")
    video_feature_extractor = AutoProcessor.from_pretrained(video_model_name)
    
    multi_test = MultimodalDataset(
        test_text,
        test_video,
        test_audio,
        tokenizer,
        video_feature_extractor,
        max_len=128,
        label_dict=label2id,
        video_dir=video_path,
        data_part='test'
    )
    
    test_dataloader = DataLoader(multi_test, batch_size=bs, shuffle=True)
    
    return test_dataloader

    
seed = 42
torch.manual_seed(seed)
random.seed(seed)
np.random.seed(seed)

label2id = {
    "anger": 0,
    "disgust": 1,
    "fear": 2,
    "joy": 3,
    "neutral": 4,
    "sadness": 5,
    "surprise": 6,
}
num_labels = 7

text_path = "/test/meld_testdata/text_test_meld.csv"
audio_path = "/test/meld_testdata/audio_test_meld_opensmile_ver2.csv"
video_path = "/test/meld_testdata/Video/"

hidden_size = 512

fix_minor_mistakes()
device = 'cuda'

text_model, video_model, audio_model = prepare_models(num_labels, os.getenv("MODEL_PATH"), device=device)
test_dataloader = prepare_testdataloader(6, text_path, audio_path, video_path, label2id)

multi_model = MultimodalClassificationModel(
            text_model,
            video_model,
            audio_model,
            num_labels,
            input_size=4885,  
            hidden_size=hidden_size
)

checkpoint = torch.load(os.getenv("MULTIMODAL_MODEL"))
multi_model.load_state_dict(checkpoint)
final_model = MainModel(multi_model, device=device)

test_fscore = test(test_dataloader, final_model)
print("Взвешенная F-мера:", round(test_fscore * 100, 2))
assert test_fscore > .64
