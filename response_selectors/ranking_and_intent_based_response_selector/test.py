import requests
import json
import time
import os 

url = "http://0.0.0.0:8081/respond"

current_directory = os.path.dirname(__file__)
test_data_path = os.path.join(current_directory, 'test_sample.json')

def test_input_data_format(data):
    assert isinstance(data, dict), "Input data should be a JSON object (dictionary)"
    midas_predictions = data['dialogs'][0]['human_utterances'][0]['annotations']['combined_classification']['midas_classification']
    assert midas_predictions, 'Midas classification is missing in data'
    hypotheses = [item['text'] for item in data.get('dialogs', [{}])[0].get('human_utterances', [{}])[0].get('hypotheses', [])]
    hypotheses_annotation = [item['annotations']['combined_classification']['midas_classification'] for item in data.get('dialogs', [{}])[0].get('human_utterances', [{}])[0].get('hypotheses', [])]
    assert all([hypotheses, hypotheses_annotation]), 'Hypotheses and their midas classes are missing in the data'
    result = requests.post(url, json=data).json()
    assert result, f'Invalid format of input data'
    print("Success! Input data is in JSON format and valid.")


def test_output_data_format(data):
    result = requests.post(url, json=data).json()
    hypotheses = [
        item['text'] for dialog in data['dialogs'] 
        for utterance in dialog['utterances'] 
        for item in utterance['hypotheses']
    ]
    assert len(hypotheses) > 0, 'No hypotheses for response'
    print(f'Hypotheses for response selection: {hypotheses}')
    assert result, f'Service is not working'
    assert isinstance(result, list) and len(result) > 0, "Output list is empty"
    response_text = result[0][1]
    assert isinstance(response_text, str), "Response text is not a string"
    assert response_text in hypotheses, "Response wasn't chosen from the hypotheses"
    assert response_text.strip() != "", "Response text is empty"
    print(f"Test passed: Response is valid and not empty. Response:{response_text}")

def test_respond_time(data):
    start_time = time.time()
    requests.post(url, json=data).json()
    total_time = time.time() - start_time
    print(f"Execution Time: {total_time} s")
    
    assert total_time < 0.4, f"Expected time < 0.4s, but got {total_time}s"


if __name__ == "__main__":
    with open(test_data_path) as file:
        data = json.load(file)
    test_input_data_format(data)
    test_output_data_format(data)
    test_respond_time(data)
 
    

    
