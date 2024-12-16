import requests
import time
import allure
import pytest
import csv
import pandas as pd
from sacrebleu import BLEU
import re
import json
from server import VoicePayload

URL = "http://0.0.0.0:8333/respond"
DUMMY_JSON = {"sound_paths": ["http://files:3000/file?file=non_existent.mp3"]}

def _call_service(payload):
    time_deltas = []
    start_time = time.time()
    result = requests.post(URL, json=payload)
    stop_time = time.time()
    time_deltas.append(stop_time - start_time)
    
    result = result.json()
    my_task_id = result.get("task_id")

    caption = "Error"
    for _attempt in range(100):
        start_time = time.time()
        result = requests.post(URL, json=DUMMY_JSON)
        stop_time = time.time()
        time_deltas.append(stop_time - start_time)
        result = result.json()
        all_tasks_info = result.get('all_status')
        for t in all_tasks_info:
            if t['id'] == my_task_id:
                    current_task_info = t 
        if current_task_info['status'] == "completed": 
            caption = current_task_info.get('caption')
            caption = caption.replace("'", '"')
            caption = json.loads(caption)
            caption = caption[0]['caption']
            break
        else:
            time.sleep(5)
    
    avg_response_time = sum(time_deltas) / len(time_deltas)
    return result, caption, avg_response_time

@allure.description("""4.1.2 Test input and output data types""")
@pytest.mark.parametrize("test_in_out_data", [
    {
        "payload": {
            "sound_paths": ["http://files:3000/file?file=wav_rain.wav"],
            "sound_durations": [42],
            "sound_types": ["wav"]
        }
    },
    {
        "payload": {
            "sound_paths": ["http://files:3000/file?file=mp3_rain.mp3"],
            "sound_durations": [42],
            "sound_types": ["mp3"]
        }
    }
])
def test_in_out(test_in_out_data):
    payload = test_in_out_data["payload"]
    # check input format
    valid_extensions = [".oga", ".mp3", ".MP3", ".ogg", ".flac", ".mp4", ".wav"]
    for path in payload.get("sound_paths"):
        if path:
            assert any(path.lower().endswith(ext) for ext in valid_extensions), "Invalid input type"
            print(f"...\nSent file {payload.get('sound_paths')},\ngot correct input type") #TODO which format get
    result, caption, _  = _call_service(payload)
    assert isinstance(result, (dict, list)), "Expected result to be a JSON object or array"
    print(f"\ngot correct output type")
    print(f"\ngot response {caption}")
    
@allure.description("""4.1.3 Test execution time""")
def test_exec_time():
    test_data = {
            "sound_paths": ["http://files:3000/file?file=mp3_rain.mp3"],
            "sound_durations": [42],
            "sound_types": ["mp3"]
        }
    _, _, avg_time = _call_service(test_data)
    assert avg_time <= 0.4, "Unsufficient run time"
    print(f"...\nAverage response time is {avg_time}")

@allure.description("""BLEU test""")
def test_for_bleu():
    df_path = "https://lnsigo.mipt.ru/export/serikov/mmodal-ac/clotho_subset/subset_captions.csv"
    folder_path = "http://files:3000/file?file="
    columns = ["fname", "cap1", "cap2", "cap3", "cap4", "cap5"]
    avgs = []
    lenss = []

    #добавление колонки preds из результатов работы модели
    df = pd.read_csv(df_path)
	#добавление заголовков в таблицу пока без pred
    df.columns = columns
	#а вот тут уже pred выделяются из аутпута модели
    predictions = []
    for value in df['fname']:
        file_name = re.sub(r"^[^\w\d.]+|[^\w\d.]+$", "",value)
        file_name = file_name.replace(" ", "_")
        sound_paths = folder_path+file_name
        sound_durations = 60
        sound_types = file_name.split(".")[1]
        test_data = { "sound_paths": [sound_paths], "sound_durations": [sound_durations], "sound_types": [sound_types]}

        _, prediction, _ = _call_service(test_data)
        predictions.append(prediction)
        
    
    df['pred'] = predictions
    df_new_path = "./voice_with_predictions.csv"
    df.to_csv(df_new_path, index=False)
    columns += ['pred']
    
    # расчет метрики блю
    for row in csv.DictReader(open(df_new_path), fieldnames=columns):
        lens = []
        for col in columns:
            row[col] = row[col].strip()
        src_col='pred'
        src_text = row[src_col]
        tgt_texts = [row[c] for c in columns if c not in ['fname',src_col]]
        bleu = BLEU()
        bleus = [bleu.corpus_score([src_text], [[tgt_text]]).score for tgt_text in tgt_texts]
        [lens.append(len(tgt_text.split())) for tgt_text in tgt_texts]
        avg_bleu = sum(bleus)/len(bleus)
        avgs.append(avg_bleu)
        lenss.append(sum(lens)/len(lens))

    print(f"...\nBLEU metric value is", sum(avgs)/len(avgs))

if __name__ == "__main__":
    test_in_out()
    test_exec_time()
    test_for_bleu()
