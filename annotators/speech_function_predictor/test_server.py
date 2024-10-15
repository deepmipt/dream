import requests
import os
import allure

SERVICE_PORT = os.getenv("SERVICE_PORT")
URL = f"http://0.0.0.0:{SERVICE_PORT}"
MODEL_URL = f"{URL}/model"
ANNOTATION_URL = f"{URL}/annotation"


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


@allure.description("Test annotation hypothesis and check that input is a list of strings")
def test_annotation_hypothesis():
    annotation_test_data = ["Reply.Acknowledge"]
    validate_input(annotation_test_data)
    annotation_hypothesis = requests.post(ANNOTATION_URL, json=annotation_test_data).json()
    print("test name: sfp annotation_hypothesis")
    assert annotation_hypothesis == [{"batch": [{}]}]


if __name__ == "__main__":
    test_model_hypothesis()
    test_annotation_hypothesis()
    print("Success")
