import requests
import tempfile
import os
import subprocess
import pandas as pd
import time
import allure
from sklearn.metrics import f1_score

SERVICE_PORT = 8108
URL = f"http://0.0.0.0:{SERVICE_PORT}"
data_path = "http://files.deeppavlov.ai/tmp/sf.tar.gz"


def time_test(limit=4):
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            assert duration < limit, f"Test took too long: {duration:.2f} seconds"
            print(f"{func.__name__} passed. Execution time: {duration:.2f} seconds")
            return result
        return wrapper
    return decorator

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

@allure.description("Test that weighted F1 score is higher than 0.7")
@time_test(limit=4)
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
    print(f"Weighted F1 score: {f1_weighted}")
    assert f1_weighted > 0.7, f"F1 score too low: {f1_weighted}"

@allure.description("Test model with one previous phrase")
@time_test(limit=4)
def test_model_with_one_previous_phrase():
    
    model_test_data = {
        "phrases": ["fine, thank you. and you?"],
        "prev_phrases": ["How are you doing today?"],
        "prev_speech_functions": ["Open.Demand.Fact"],
    }
    
    model_hypothesis = requests.post(f"{URL}/respond", json=model_test_data).json()
    
    assert model_hypothesis == ["React.Rejoinder.Support.Response.Resolve"], f"Unexpected response: {model_hypothesis}"

@allure.description("Test launch time")
def test_component_launch_time():
    model_test_data = {
        "phrases": ["fine, thank you. and you?"],
        "prev_phrases": ["How are you doing today?"],
        "prev_speech_functions": ["Open.Demand.Fact"],
    }
    start_time = time.time()
    response = False
    while True:
        try:
            current_time = time.time()
            response = requests.post(URL, json=model_test_data).status_code == 200
            if response:
                break
        except Exception as e:
            print(f"Exception occurred: {e}")
            current_time = time.time()
            if current_time - start_time < 20 * 60: 
                time.sleep(15)
                continue
            else:
                break
    assert response

    
@allure.description("Test annotation with several previous phrases")
@time_test(limit=4)
def test_annotation_with_batches():
    
    annotation_test_data = {
        "phrases": ["Thank you!", "You're just stunning."],
        "prev_phrases": ["Hi!", "You look wonderful today."],
        "prev_speech_functions": ["Open.Attend", "Open.Demand.Fact"],
    }
    
    annotation_hypothesis = requests.post(f"{URL}/respond_batch", json=annotation_test_data).json()

    assert annotation_hypothesis == [
        {"batch": ["React.Respond.Support.Reply.Accept", "Sustain.Continue.Prolong"]}
    ], f"Unexpected response: {annotation_hypothesis}"

@allure.description("Test annotation with no previous context")
@time_test(limit=4)
def test_annotation_no_previous_context():
    model_test_data = {
        "phrases": ["Hi, Helen!"],
        "prev_phrases": [""],
        "prev_speech_functions": [""],
    }

    model_hypothesis = requests.post(f"{URL}/respond", json=model_test_data).json()

    assert model_hypothesis == ["Open.Attend"], f"Unexpected response: {model_hypothesis}"

if __name__ == "__main__":
    
    test_model_with_one_previous_phrase()
    test_annotation_with_batches()
    test_annotation_no_previous_context()
    test_weighted_f1_score()
    test_component_launch_time()
