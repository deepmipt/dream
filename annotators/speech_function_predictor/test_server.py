import requests
import os
import allure
import time

SERVICE_PORT = os.getenv("SERVICE_PORT")
URL = f"http://0.0.0.0:{SERVICE_PORT}"
MODEL_URL = f"{URL}/model"

@allure.description("Test model input")
def validate_input(input_data):
    assert isinstance(input_data, list), "Input data must be a list"
    assert all(isinstance(item, str) for item in input_data), "All elements in the list must be strings"


@allure.description("Test model hypothesis and check that input is a list of strings")
def test_model_hypothesis():
    model_test_data = ["Reply.Acknowledge"]
    validate_input(model_test_data)
    model_hypothesis = requests.post(MODEL_URL, json=model_test_data).json()
    print("test name: sfp model_hypothesis")
    assert model_hypothesis == [{}]


@allure.description("Test launch time")
def test_launch_time():
    test_data = ["Reply.Acknowledge"]
    
    start_time = time.time()
    response = False
    while True:
        try:
            current_time = time.time()
            response = requests.post(MODEL_URL, json=test_data).status_code == 200
            if response:
                break
        except Exception as e:
            print(f"Exception occurred: {e}")
            current_time = time.time()
            if current_time - start_time < 20 * 60:  # < 20 minutes
                time.sleep(15)
                continue
            else:
                break
    assert response

@allure.description("Test execution time")
def test_execution_time():
    test_data = ["Reply.Acknowledge"]
    
    start_time = time.time()

    model_hypothesis = requests.post(MODEL_URL, json=test_data).json()
    total_duration = time.time() - start_time
    print(model_hypothesis)
    print(f"Total execution time: {total_duration:.2f} seconds")
    assert total_duration < 4 , f"Execution time too long: {total_duration:.2f} seconds"


if __name__ == "__main__":
    test_model_hypothesis()
    test_launch_time()
    test_execution_time()
    print("Success")
