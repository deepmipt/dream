import requests
import time

SERVICE_PORT = 8107
URL = f"http://0.0.0.0:{SERVICE_PORT}"
MODEL_URL = f"{URL}/respond"

test_data = {'phrases': 'Hi!',
    'funcs': ['Open.Attend']}

def validate_input(input_data):
    assert all(isinstance(phrase, str) for phrase in input_data["phrases"]), 'Phrases must be Unicode strings'
    assert isinstance(input_data, dict), "Input data must be a dictionary"
    assert "funcs" in input_data, "Input data must contain 'funcs' key"
    assert isinstance(input_data["funcs"], list), "'funcs' must be a list of strings"
    print("Input data is valid and in JSON format")


def test_model_hypothesis():
    validate_input(test_data)
    response = requests.post(MODEL_URL, json=test_data)
    
    print("Test name: sfp model_hypothesis")
    assert response.status_code == 200, "Response code should be 200 OK"
    
    response_data = response.json()[0]
    
    assert isinstance(response_data, list), "Response should be a list"
    
    for prediction in response_data:
        assert isinstance(prediction, dict), "Each item in response should be a dictionary"
        assert "prediction" in prediction, "Missing 'prediction' in response"
        assert "confidence" in prediction, "Missing 'confidence' in response"
    
    print("Output data is valid")
    print(f"Response:{response_data}")

def test_execution_time():
    start_time = time.time()
    response = requests.post(MODEL_URL, json=test_data)
    total_duration = time.time() - start_time
    print(f"Total execution time: {total_duration:.2f} seconds")
    assert total_duration < 0.4, f"Execution time too long: {total_duration:.2f} seconds"
    assert response.status_code == 200, "Response code should be 200 OK"

if __name__ == "__main__":
    validate_input(test_data)
    test_model_hypothesis()
    test_execution_time()
    print("All tests passed successfully")


