import allure
import csv
from sacrebleu import BLEU
import pandas as pd
import requests

URL = "http://0.0.0.0:8069/respond"

@allure.description("""BLEU test""")
def test_for_bleu():
    df_path = "https://lnsigo.mipt.ru/export/serikov/mmodal-ac/cc3m_subset/fromage_predictions.csv"
    folder_path = "https://lnsigo.mipt.ru/export/serikov/mmodal-ac/cc3m_subset/"
    columns = ["fname", "cap1", "cap2", "cap3", "cap4", "cap5"]
    avgs = []
    lenss = []

    df = pd.read_csv(df_path)
    df.columns = columns
    predictions = []

    for value in df['fname']:
        sentences = [""]
        image_paths = [folder_path+value]
        test_data = {"image_paths": image_paths, "sentences": sentences}
        prediction = requests.post(URL, json=test_data)
        predictions.append(prediction.json())
    
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
    test_for_bleu()