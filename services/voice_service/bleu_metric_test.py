from sacrebleu import BLEU
import allure
import csv
import pandas as pd
import requests
import json
import re

URL = "http://0.0.0.0:8333/respond"

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
        file_name = file_name.replace(" ", "%20")
        sound_paths = folder_path+file_name
        sound_durations = 60
        sound_types = file_name.split(".")[1]
        test_data = { "sound_paths": [sound_paths], "sound_durations": [sound_durations], "sound_types": [sound_types]}
        prediction = requests.post(URL, json=test_data)
        while prediction.json() and not prediction.json()[0].get("response"):
            prediction = requests.post(URL, json={})
        predictions.append(prediction.json()[0]['response'][0]['caption'])
    
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
    test_for_bleu()
