import requests
import time
import subprocess
import allure
import json

url = "http://0.0.0.0:8045/respond"

@allure.description("""4.1.2 Test input and output data types""")
def test_in_out():
    video_path = "http://files:3000/file?file=file_228.mp4"
    test_data = { "video_paths": [video_path], "video_durations": [59], "video_types": ['.mp4']}
    result = requests.post(url, json=test_data)
    valid_extensions = ['.mp4']
    assert any(test_data["video_paths"][0].lower().endswith(ext) for ext in valid_extensions), "Invalid input type"
    assert isinstance(result.json(), (dict, list)), "Expected result to be a JSON object or array"

@allure.description("""4.1.3 Test execution time""")
def test_exec_time():
    video_path = "http://files:3000/file?file=file_228.mp4"
    test_data = { "video_paths": [video_path], "video_durations": [59], "video_types": ['.mp4']}    
    start_time = time.time()
    result = requests.post(url, json=test_data)
    assert time.time() - start_time <= 0.4, "Unsufficient run time"

@allure.description("""Simple execution test""")
def test_execution():
    video_path = "http://files:3000/file?file=file_228.mp4"
    gold_result = [{'video_captioning_chapters': "[{'sentence': 'Intro.', 'timestamp': [0.0, 10.727636363636364]}, {'sentence': 'Showing impressive award combinations.', 'timestamp': [10.727636363636364, 30.3949696969697]}, {'sentence': 'Discussing who won an Oscar and a gold medal.', 'timestamp': [30.3949696969697, 59.002]}]\n"}]
    test_data = { "video_paths": [video_path], "video_durations": [59], "video_types": ['.mp4']} 
    result = requests.post(url, json=test_data)
    assert result.json() == gold_result

if __name__ == "__main__":
    test_in_out()
    test_exec_time()
    test_execution()