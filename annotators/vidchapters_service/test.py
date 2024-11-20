import requests
import time
import subprocess
import allure
import json

URL = "http://0.0.0.0:8045/respond"
DUMMY_JSON = {"video_paths": ["http://files:3000/file?file=non_existent.mp4"]}

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
            caption = caption[0]['caption']

            assert isinstance(result, (dict, list)), "Expected result to be a JSON object or array"

            break
        else:
            time.sleep(10)
    
    avg_response_time = sum(time_deltas) / len(time_deltas)
    return caption, avg_response_time

@allure.description("""4.1.2 Test input and output data types""")
def test_in_out():
    video_path = "https://raw.githubusercontent.com/deeppavlov/mmodal_files_bkp/refs/heads/main/medals.mp4"
    test_data = { 
        "video_paths": [video_path], 
        "video_durations": [59], 
        "video_types": ['.mp4']
    }
    valid_extensions = ['.mp4']
    for path in test_data.get("video_paths"):
        if path:
            assert any(path.lower().endswith(ext) for ext in valid_extensions), "Invalid input type"
            print(f"...\nSent file {test_data.get('video_paths')},\ngot correct input type") #TODO which format get
    caption, _  = _call_service(test_data)
    print(f"...\nSent file {test_data.get('video_paths')},\ngot response {caption}")  
    # assert any(test_data["video_paths"][0].lower().endswith(ext) for ext in valid_extensions), "Invalid input type"
    # assert isinstance(result.json(), (dict, list)), "Expected result to be a JSON object or array"
    # print(f"...\nSent file {video_path},\ngot response {result.json()[0].get("response")}")

@allure.description("""4.1.3 Test execution time""")
def test_exec_time():
    video_path = "https://raw.githubusercontent.com/deeppavlov/mmodal_files_bkp/refs/heads/main/medals.mp4"
    test_data = { 
        "video_paths": [video_path], 
        "video_durations": [59], 
        "video_types": ['.mp4']
    }    
    _, avg_time = _call_service(test_data)
    assert avg_time <= 0.4, "Unsufficient run time"
    print(f"...\nAverage response time is {avg_time}")
    

if __name__ == "__main__":
    test_in_out()
    test_exec_time()
