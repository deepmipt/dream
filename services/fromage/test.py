import requests
import time
import subprocess
import allure
import pytest
import allure
import csv
from sacrebleu import BLEU
import pandas as pd

URL = "http://0.0.0.0:8069/respond"

@allure.description("""4.1.2 Test input and output data types""")
@pytest.mark.parametrize("test_in_out_data", [
    {
        "image_paths": ["https://raw.githubusercontent.com/deeppavlov/mmodal_files_bkp/refs/heads/main/car.jpg"], 
        "sentences": [""]
    },
    {
        "image_paths": ["https://raw.githubusercontent.com/deeppavlov/mmodal_files_bkp/refs/heads/main/dogs.png"], 
        "sentences": [""]
    }
])
def test_in_out(test_in_out_data):
    result = requests.post(URL, json=test_in_out_data)
    while result.json() and not result.json()[0].get("response"):
        result = requests.post(URL, json={})
    valid_extensions = ['.jpeg', '.jpg', '.png']
    for path in test_in_out_data['image_paths']:
        assert any(path.lower().endswith(ext) for ext in valid_extensions), "Invalid input type"
    assert isinstance(result.json(), (dict, list)), "Expected result to be a JSON object or array"
    print(f"...\nSent file {test_in_out_data['image_paths'][0]},\ngot response {result.json()}")


@allure.description("""4.1.3 Test execution time""")
def test_exec_time():
    image_paths = ["https://raw.githubusercontent.com/deeppavlov/mmodal_files_bkp/refs/heads/main/car.jpg"]
    sentences = [""]
    test_data = { "image_paths": image_paths, "sentences": sentences}
    start_time = time.time()
    result = requests.post(URL, json=test_data)
    end_time = time.time() - start_time
    while result.json() and not result.json()[0].get("response"):
        result = requests.post(URL, json={})
    assert end_time <= 0.4, "Unsufficient run time"
    print(f"...\nAverage response time is {end_time}")

@allure.description("""BLEU test""")
def test_for_bleu():
    df_path = "https://lnsigo.mipt.ru/export/serikov/mmodal-ac/cc3m_subset/fromage_predictions.csv"
    folder_path = "https://lnsigo.mipt.ru/export/serikov/mmodal-ac/cc3m_subset/"
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
        sentences = [""]
        image_paths = [folder_path+value]
        test_data = {"image_paths": image_paths, "sentences": sentences}
        prediction = requests.post(URL, json=test_data)
        while prediction.json() and not prediction.json()[0].get("response"):
            prediction = requests.post(URL, json={})
        
        predictions.append(prediction.json()[0].get("response"))

    df['pred'] = predictions
    df_new_path = "./fromage_with_predictions.csv"
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
