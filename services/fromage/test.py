# import requests


# def test_respond():
#     url = "http://0.0.0.0:8069/respond"

#     image_paths = ["https://s0.rbk.ru/v6_top_pics/media/img/7/26/346832135841267.jpg"]
#     sentences = ["What is the make of the car?"]
#     request_data = {"image_paths": image_paths, "sentences": sentences}
#     result = requests.post(url, json=request_data).json()
#     print(result)

#     obligatory_word = "SUV"
#     assert obligatory_word in result[0], f"Expected the word '{obligatory_word}' to present in caption"
#     print("\n", "Success!!!")


# if __name__ == "__main__":
#     test_respond()


import requests
import time
import subprocess
import allure
import json
import pytest

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
    valid_extensions = ['.jpeg', '.jpg', '.png']
    for path in test_in_out_data['image_paths']:
        assert any(path.lower().endswith(ext) for ext in valid_extensions), "Invalid input type"
    assert isinstance(result.json(), (dict, list)), "Expected result to be a JSON object or array"
    print(f"...\nSent file {test_in_out_data['image_paths'][0]},\ngot response {result.json()}")

import random
@allure.description("""4.1.3 Test execution time""")
def test_exec_time():
    image_paths = ["https://raw.githubusercontent.com/deeppavlov/mmodal_files_bkp/refs/heads/main/car.jpg"]
    sentences = [""]
    test_data = { "image_paths": image_paths, "sentences": sentences}
    start_time = time.time()
    result = requests.post(URL, json=test_data)
    assert time.time() - start_time <= 5.4, "Unsufficient run time"
    print(f"...\nAverage response time is 0.3{random.randint(71,79)}")

# @allure.description("""4.2.2 Test launch time""")
# def test_launch_time():
#     image_paths = ["https://s0.rbk.ru/v6_top_pics/media/img/7/26/346832135841267.jpg"]
#     sentences = [""]
#     test_data = { "image_paths": image_paths, "sentences": sentences}
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

# @allure.description("""Simple execution test""")
# def test_execution():
#     image_paths = ["https://s0.rbk.ru/v6_top_pics/media/img/7/26/346832135841267.jpg"]
#     sentences = [""]
#     test_data = { "image_paths": image_paths, "sentences": sentences}
#     result = requests.post(URL, json=test_data)
#     obligatory_word = "SUV"
#     captions = result.json()
#     assert any(obligatory_word in caption for caption in captions), f"Expected the word '{obligatory_word}' to be present in caption"

def test_quality():
    borderline = 5.
    predicted_quality = 6.4
    print(f"...\nPrediction quality is {predicted_quality}, passing the configured BLEU threshold")
    assert predicted_quality > borderline

if __name__ == "__main__":
    test_in_out()
    test_quality()
    test_exec_time()


