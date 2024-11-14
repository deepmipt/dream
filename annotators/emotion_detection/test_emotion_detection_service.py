import requests
import os
import time


SERVICE_PORT = 8040 
URL = f"http://0.0.0.0:{SERVICE_PORT}/model"


def test_launch_time(request_data):
    start_time = time.time()
    response = False

    while True:
        try:
            current_time = time.time()
            response = requests.post(URL, json=request_data)
            if response.status_code == 200:
                break

        except Exception as e:
            current_time = time.time()
            if current_time - start_time < 20 * 60: # < 20 minutes
                time.sleep(2)
                continue
            else:
                raise TimeoutError("Couldn't build the component")
    
    while response.json() and not response.json()[0].get("emotion"):
        response = requests.post(URL, json={
            "text": [], 
            "video_path": [] 
        })

    assert response.status_code == 200
    print('Launch test completed in', current_time - start_time, 'seconds')


def test_correct_emotion_guess(request_data, gold_results):
    response = requests.post(URL, json=request_data)
    while response.json() and not response.json()[0].get("emotion"):
        response = requests.post(URL, json={
            "text": [], 
            "video_path": [] 
        })
    assert response.json()[0]["emotion"] == gold_results[0]
    print('Correct emotion detected:', response.json()[0]["emotion"])
    
    
def test_emotion_is_base_emotion(request_data):
    response = requests.post(URL, json=request_data)
    while response.json() and not response.json()[0].get("emotion"):
        response = requests.post(URL, json={
            "text": [], 
            "video_path": [] 
        })
    assert response.json()[0]["emotion"] in ["anger", "disgust", "fear", "joy", "neutral", "sadness", "surprise"]
    print('Emotion', response.json()[0]["emotion"], 'is Eckmans basic emotion (["anger", "disgust", "fear", "joy", "neutral", "sadness", "surprise"])')
    
    
def test_response_is_json(request_data):
    response = requests.post(URL, json=request_data)
    while response.json() and not response.json()[0].get("emotion"):
        response = requests.post(URL, json={
            "text": [], 
            "video_path": [] 
        })
    assert isinstance(response.json(), list)
    print('Response is json:', response.json())
    
    
def test_response_time(request_data):
    times = []
    start = time.time()
    response = requests.post(URL, json=request_data)
    end = time.time()
    times.append(end - start)
    while response.json() and not response.json()[0].get("emotion"):
        start = time.time()
        response = requests.post(URL, json={
            "text": [], 
            "video_path": [] 
        })
        times.append(time.time() - start)
    print('Response time:', end - start, 'Times:', times)
    assert (end - start) <= 0.4  
    
    
if __name__ == '__main__':
    request_data = {
        "text": 
        ["They treat me like a cow. A beef cow. And I'm a... people!"], 
        "video_path": 
        ["emotion_detection_samples/angry_man.mp4"] 
    }
    gold_results = ["anger"]
    print('Request:', request_data)
    print('Gold results:', gold_results)
    test_launch_time(request_data)
    test_response_time(request_data)
    test_response_is_json(request_data)
    test_correct_emotion_guess(request_data, gold_results)
    test_emotion_is_base_emotion(request_data)