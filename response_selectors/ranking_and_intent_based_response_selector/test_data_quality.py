import requests
import json
import os
import tarfile


current_directory = os.path.dirname(__file__)
file_path = os.path.join(current_directory, 'midas_dialogs.tar.gz')

with tarfile.open(file_path, 'r:gz') as tar:
    file1 = tar.extractfile('content/dialogs_with_midas.json')
    file2 = tar.extractfile('content/dialogs_without_midas.json')
    if file1 and file2:
        midas_data = json.load(file1)
        no_midas_data = json.load(file2)

LLM_eval_prompt = """
Evaluate the following dialogue on a continuous scale from 0.0 to 5.0.

Dialogue: {dialogue}

Please rate the dialogue based on the following dimensions:

- **Appropriateness**: How well do the responses fit the context and flow of the conversation?
- **Content**: How informative and coherent is the dialogue overall?
- **Grammar**: How grammatically correct are the responses throughout the dialogue?
- **Relevance**: How relevant are the responses to the topics discussed in the conversation?

Provide the evaluation in JSON format with scores for each dimension.
"""

def normalize_text(data):
    for k in data.keys():
        dialog = data[k]
        for i in range(len(dialog)):
            if isinstance(dialog[i].get('text'), list) and dialog[i]['text']:
                dialog[i]['text'] = dialog[i]['text'][0].replace('#+','')
    return data

normalized_midas_data = normalize_text(midas_data)
normalized_no_midas_data = normalize_text(no_midas_data)


def evaluate_dialogue(dialogue):
    url = "http://0.0.0.0:8145/respond"
    formatted_prompt = LLM_eval_prompt.format(dialogue=dialogue)

    request = {
         "dialog_contexts": [""],
         "prompts": [formatted_prompt],
         "openai_api_keys": [os.environ["OPENAI_API_KEY"]],
         "openai_api_bases":[os.environ["OPENAI_API_BASE"]]

    }
    result = requests.post(url, json=request)
    print(result.json())
    return result.json()
    
def calculate_overall_score(result):
    scores = json.loads(result[0][0])
    total_score = 0
    num_metrics = len(scores) 
    for key in scores.keys():
        total_score += scores[key]
    overall_score = total_score / num_metrics
    return overall_score

def compare_results(result1, result2):
    overall_score1 = calculate_overall_score(result1)
    overall_score2 = calculate_overall_score(result2)
    print(f"Overall score for a dialogue with MIDAS based component: {overall_score1:.2f}")
    print(f"Overall score for a dialogue without MIDAS based component: {overall_score2:.2f}")
    assert overall_score1 > overall_score2, f"Assertion failed: MIDAS based component score ({overall_score1:.2f}) is not higher than other component score ({overall_score2:.2f})."
    print("Success! Dialogue with MIDAS based component scored higher.")
    

if __name__ == "__main__":
    for k in normalized_midas_data.keys():
        dialogue1 = normalized_midas_data[k]
        dialogue2 = normalized_no_midas_data[k]
        midas_result = evaluate_dialogue(dialogue1)
        print(midas_result)
        print(f'Metrics for a dialogue with MIDAS based component:{json.loads(midas_result[0][0])}')
        no_midas_result = evaluate_dialogue(dialogue2)
        print(f'Metrics for a dialogue without MIDAS based component:{json.loads(no_midas_result[0][0])}')
        compare_results(midas_result, no_midas_result)