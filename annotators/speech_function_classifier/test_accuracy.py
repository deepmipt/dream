import requests
import tempfile
import os
import subprocess
import pandas as pd
import allure
from sklearn.metrics import f1_score

SERVICE_PORT = 8108
URL = f"http://0.0.0.0:{SERVICE_PORT}"
data_path = "http://files.deeppavlov.ai/tmp/sf.tar.gz"



def check_sfs(predicted_sf, previous_sf, current_speaker, previous_speaker):
    if predicted_sf == "Command":
        if ("Open" in previous_sf or previous_sf == "") and current_speaker == previous_speaker:
            return "Open.Command"
        elif current_speaker == previous_speaker:
            return "Sustain.Continue.Command"
        else:
            return "React.Respond.Command"
    elif predicted_sf == "Engage":
        if previous_sf == "":
            return "Open.Attend"
        else:
            return "React.Respond.Support.Engage"
    return predicted_sf

def setup_data():
    """Setup temporary directory, download and extract the data"""
    temp_dir = tempfile.mkdtemp()
    with open(os.path.join(temp_dir, "data.tar.gz"), "wb") as fout:
        fout.write(requests.get(data_path).content)
    subprocess.check_call("tar -xzf data.tar.gz", shell=True, cwd=temp_dir)
    
    df = pd.read_csv(os.path.join(temp_dir, 'sf/test.csv'))
    return df

@allure.description("Test that weighted F1 score is higher than 70") 

def test_weighted_f1_score():
    
    df = setup_data()
    predicted_labels = []
    true_labels = []
    for _, row in df.iterrows():
        prev_phrase = row['prev_utterance']
        cur_phrase = row['current_utterance']
        cur_speaker = row['current_speaker']
        prev_speaker = row['prev_speaker']
        if isinstance(row['prev_sf'], float):
            prev_sf = ""
        else:
            prev_sf = row['prev_sf']

        cur_sf = check_sfs(row["current_sf"], prev_sf, cur_speaker, prev_speaker)
        model_test_data = {
            "phrases": [cur_phrase],
            "prev_phrases": [prev_phrase],
            "prev_speech_functions": [prev_sf],
        }
        
        model_response = requests.post(f"{URL}/respond", json=model_test_data).json()
        predicted_labels.extend(model_response)
        true_labels.append(cur_sf)
   
    f1_weighted = f1_score(true_labels, predicted_labels, average='weighted')
    print(f"Weighted F1 score: {f1_weighted*100}%")
    assert f1_weighted*100 > 70, f"F1 score too low: {f1_weighted*100}%"



if __name__ == "__main__":
    
    test_weighted_f1_score()
    print('Success!')
