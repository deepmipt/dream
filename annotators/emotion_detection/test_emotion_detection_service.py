import requests
import os
import time


SERVICE_PORT = 8040 
URL = f"http://0.0.0.0:{SERVICE_PORT}/model"


def _service_call(request):
    time_deltas = []
    start_time = time.time()
    response = requests.post(URL, json=request)
    stop_time = time.time()
    time_deltas.append(stop_time - start_time)
    
    my_task_id = response.json().get("task_id")
    
    while not response.json().get("result"):
        start_time = time.time()
        response = requests.post(URL, json={
            "text": [], 
            "video_path": [],
            "task_id": [my_task_id]
        })
        stop_time = time.time()
        time_deltas.append(stop_time - start_time)
        
    avg_response_time = sum(time_deltas) / len(time_deltas)
    
    return response, avg_response_time


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

    my_task_id = response.json().get("task_id")
    
    while not response.json().get("result"):
            response = requests.post(URL, json={
                "text": [], 
                "video_path": [],
                "task_id": [my_task_id]
            })

    assert response.status_code == 200
    print('Launch test completed in', current_time - start_time, 'seconds')


def test_correct_emotion_guess(request_data, gold_results):
    response, _ = _service_call(request_data)
    assert response.json().get("result") == gold_results
    print('Correct emotion detected:', response.json().get("result"))
    
    
def test_emotion_is_base_emotion(request_data):
    response, _ = _service_call(request_data)
    assert response.json().get("result")[0] in ["anger", "disgust", "fear", "joy", "neutral", "sadness", "surprise"]
    print('Emotion', response.json().get("result")[0], 'is Eckmans basic emotion (["anger", "disgust", "fear", "joy", "neutral", "sadness", "surprise"])')
    
    
def test_response_is_json(request_data):
    response, _ = _service_call(request_data)
    assert isinstance(response.json(), dict)
    print('Response is json:', response.json())
    
    
def test_response_time(request_data):
    _, avg_time = _service_call(request_data)
    print('Response time:', avg_time)
    assert avg_time <= 0.4  
    
    
if __name__ == '__main__':
    request_data = {
        "text": 
        ["I'm already broken"], 
        "video_path": 
        ["/data/emotion_detection_samples/sad_peaky_blinders.mp4"] 
    }
    gold_results = ["anger"]
    print('Request:', request_data)
    print('Gold results:', gold_results)
    test_launch_time(request_data)
    test_response_time(request_data)
    test_response_is_json(request_data)
    test_correct_emotion_guess(request_data, gold_results)
    test_emotion_is_base_emotion(request_data)
