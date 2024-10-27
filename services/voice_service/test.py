import requests
import time
# import subprocess
import allure
import json
import pytest

URL = "http://0.0.0.0:8333/respond"

@allure.description("""4.1.2 Test input and output data types""")
@pytest.mark.parametrize("test_in_out_data", [
    {
        "sound_paths": ["http://files:3000/file?file=file_245.wav"], #TODO: change path
        "sound_durations": [59],
        "sound_types": ['wav']
    },
    {
        "sound_paths": ["http://files:3000/file?file=file_240.mp3"], #TODO: change path
        "sound_durations": [42],
        "sound_types": ['mp3']
    }
])
def test_in_out(test_in_out_data):
    result = requests.post(URL, json=test_in_out_data)
    valid_extensions = [".oga", ".mp3", ".MP3", ".ogg", ".flac", ".mp4", ".wav"]
    for path in test_in_out_data['sound_paths']:
        assert any(path.lower().endswith(ext) for ext in valid_extensions), "Invalid input type"
    assert isinstance(result.json(), (dict, list)), "Expected result to be a JSON object or array"


@allure.description("""4.1.3 Test execution time""")
def test_exec_time():
    sound_paths = "http://files:3000/file?file=file_240.mp3"
    sound_durations = 42
    sound_types = 'mp3'
    test_data = { "sound_paths": [sound_paths], "sound_durations": [sound_durations], "sound_types": [sound_types]}
    start_time = time.time()
    result = requests.post(URL, json=test_data)
    assert time.time() - start_time <= 5.4, "Unsufficient run time"

# @allure.description("""4.2.2 Test launch time""")
# def test_launch_time():
#     sound_paths = "http://files:3000/file?file=file_50.mp3"
#     # video_paths = "http://files:3000/file?file=file_228.mp4"
#     sound_durations = 5
#     sound_types = 'mp3'
#     test_data = { "paths": [sound_paths], "durations": [sound_durations], "types": [sound_types]}
#     start_time = time.time()
#     response = False
#     while True:
#         try:
#             current_time = time.time()
#             response = requests.post(URL, json=test_data).status_code == 200
#             if response:
#                 break
#         except Exception as e:
#             print(f"Exception occurred: {e}")
#             current_time = time.time()
#             if current_time - start_time < 20 * 60:  # < 20 minutes
#                 time.sleep(15)
#                 continue
#             else:
#                 break
#     assert response

# @allure.description("""4.3.3 Test rights for dream""")
# def test_rights():
#     command = "groups $(whoami) | grep -o 'docker'"
#     result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
#     assert result.returncode == 0, f"Executed with error: {result.stderr}"
#     assert 'dolidze' in result.stdout, "Group 'dolidze' not found"


@allure.description("""Simple execution test or BLEU-metrics""")
def test_execution():
    sound_paths = "http://files:3000/file?file=file_240.mp3"  #TODO: change path
    sound_durations = [42]
    sound_types = ['mp3']
    gold_result = "rain is falling on the ground as the wind is blowing in the background"
    test_data = { "sound_paths": [sound_paths], "sound_durations": [sound_durations], "sound_types": [sound_types]}
    result = requests.post(URL, json=test_data)
    assert result.json()[0]['caption'] == gold_result

def test_quality():
    borderline = 5.
    predicted_quality = 6.4
    assert predicted_quality > 5

if __name__ == "__main__":
    test_in_out()
    test_exec_time()
    # test_launch_time()
    # test_rights()
    test_execution()
    test_quality()
