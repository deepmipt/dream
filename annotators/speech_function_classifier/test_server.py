import requests
import time
import allure

SERVICE_PORT = 8108
URL = f"http://0.0.0.0:{SERVICE_PORT}"


def time_test(limit=0.4):
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



@time_test(limit=0.4)
def test_model_with_one_previous_phrase():
    
    model_test_data = {
        "phrases": ["fine, thank you. and you?"],
        "prev_phrases": ["How are you doing today?"],
        "prev_speech_functions": ["Open.Demand.Fact"],
    }
    assert all(isinstance(phrase, str) for phrase in model_test_data["phrases"]), 'Phrases must be Unicode strings'
    assert isinstance(model_test_data, dict), 'Input data is not valid'
    print('Input data is valid and in JSON format')
    
    model_hypothesis = requests.post(f"{URL}/respond", json=model_test_data).json()
    
    assert model_hypothesis == ["React.Rejoinder.Support.Response.Resolve"], f"Unexpected response: {model_hypothesis}"

    

@allure.description("Test annotation with no previous context")
@time_test(limit=0.4)
def test_annotation_no_previous_context():
    model_test_data = {
        "phrases": ["Hi, Helen!"],
        "prev_phrases": [""],
        "prev_speech_functions": [""],
    }

    model_hypothesis = requests.post(f"{URL}/respond", json=model_test_data).json()

    assert model_hypothesis == ["Open.Attend"], f"Unexpected response: {model_hypothesis}"
    print('Test annotation with no previous context was successful')

if __name__ == "__main__":
    
    test_model_with_one_previous_phrase()
    test_annotation_no_previous_context()
    print('Success!')
