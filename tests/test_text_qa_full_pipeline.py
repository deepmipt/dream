import os
import requests

import allure
import pytest

import time
import numpy as np
from tqdm import tqdm

import string
import re
from collections import Counter
from typing import List
import sys

import json
from unidecode import unidecode

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FACT_CLS_PORT = 8087
FACT_RETRIEVAL_PORT = 8100
TEXT_QA_PORT = 8078


#################################### AUXILARY ####################################

def answer_question(question, check_factoid=True):
    questions = [question]
    
    if check_factoid:
        url = "http://0.0.0.0:{}/model".format(FACT_CLS_PORT)
        response_factoid = requests.post("http://0.0.0.0:{}/model".format(FACT_CLS_PORT), json={"sentences": questions}).json()
        if response_factoid[0]['factoid_classification']['is_factoid'] < 0.8:
            questions = []

    facts = requests.post("http://0.0.0.0:{}/model".format(FACT_RETRIEVAL_PORT), json = {"human_sentences": questions}).json()
    answer = requests.post("http://0.0.0.0:{}/model".format(TEXT_QA_PORT), json={"question_raw": questions, "top_facts": facts}).json()
    return answer


#################################### METRICS CALCULATION ####################################

def normalize_answer(s: str) -> str:
    def remove_articles(text):
        return re.sub(r'\b(a|an|the)\b', ' ', text)

    def white_space_fix(text):
        return ' '.join(text.split())

    def remove_punc(text):
        exclude = set(string.punctuation)
        return ''.join(ch for ch in text if ch not in exclude)

    def lower(text):
        return text.lower()

    s = unidecode(s)

    return white_space_fix(remove_articles(remove_punc(lower(s))))


def squad_v1_f1(y_true: List[List[str]], y_predicted: List[str]) -> float:
    """ Calculates F-1 score between y_true and y_predicted
        F-1 score uses the best matching y_true answer
        Skips examples without an answer.
    Args:
        y_true: list of correct answers (correct answers are represented by list of strings)
        y_predicted: list of predicted answers
    Returns:
        F-1 score : float
    """
    f1_total = 0.0
    count = 0
    for ground_truth, prediction in zip(y_true, y_predicted):
        if len(ground_truth[0]) == 0:
            # skip empty answers
            continue
        count += 1
        prediction_tokens = normalize_answer(prediction).split()
        f1s = []
        for gt in ground_truth:
            gt_tokens = normalize_answer(gt).split()
            common = Counter(prediction_tokens) & Counter(gt_tokens)
            num_same = sum(common.values())
            if num_same == 0:
                f1s.append(0.0)
                continue
            precision = 1.0 * num_same / len(prediction_tokens)
            recall = 1.0 * num_same / len(gt_tokens)
            f1 = (2 * precision * recall) / (precision + recall)
            f1s.append(f1)
        f1_total += max(f1s)
    return 100 * f1_total / count if count > 0 else 0


def squad_v1_exact_match(y_true: List[List[str]], y_predicted: List[str]) -> float:
    """ Calculates Exact Match score between y_true and y_predicted
        EM score uses the best matching y_true answer:
            if y_pred equal at least to one answer in y_true then EM = 1, else EM = 0
        Skips examples without an answer.
    Args:
        y_true: list of correct answers (correct answers are represented by list of strings)
        y_predicted: list of predicted answers
    Returns:
        exact match score : float
    """
    EM_total = 0
    count = 0
    for ground_truth, prediction in zip(y_true, y_predicted):
        if len(ground_truth[0]) == 0:
            # skip empty answers
            continue
        count += 1
        EMs = [int(normalize_answer(gt) == normalize_answer(prediction)) for gt in ground_truth]
        EM_total += max(EMs)
    return 100 * EM_total / count if count > 0 else 0


#################################### TESTS ####################################

@allure.description("""Test text-qa service launch time""")
@pytest.mark.parametrize(
    "question, gold_result",
    [
        (
            "Who was the first man in space?",
            "Yuri Gagarin",
        ),
    ]
)
def test_text_qa_launch_time(question, gold_result):
    logger.info("Testing launch time...")
    start_time = time.time()
    response = False

    while True:
        try:
            current_time = time.time()
            response_cls = requests.post("http://0.0.0.0:{}/model".format(FACT_CLS_PORT), json={"sentences": [question]})
            response_fact_retrieval = requests.post("http://0.0.0.0:{}/model".format(FACT_RETRIEVAL_PORT), json={"human_sentences": [question]})
            response_text_qa = requests.post("http://0.0.0.0:{}/model".format(TEXT_QA_PORT), json={"question_raw": [question], "top_facts": response_fact_retrieval.json()})

            if response_cls.status_code == 200 and response_fact_retrieval.status_code == 200 and response_text_qa.status_code == 200:
                logger.info("Success!")
                logger.info("The service is fully available. Launch time took {} seconds".format(time.time() - start_time))
                break

        except Exception as e:
            logger.info("Trying to get response from the service, current waiting time is {} seconds.".format(current_time - start_time))
            current_time = time.time()
            if current_time - start_time < 20 * 60: # < 20 minutes
                time.sleep(20)
                continue
            else:
                logger.info("Fail!")
                logger.info("The service is unreachable.")
                break
    
    assert response_cls.status_code == 200 and response_fact_retrieval.status_code == 200 and response_text_qa.status_code == 200 


@allure.description("""Test output data type""")
@pytest.mark.parametrize(
    "question, gold_result",
    [
        (
            "Who was the first man in space?",
            "Yuri Gagarin",
        ),
    ]
)
def test_text_qa_json(question, gold_result):
    language = "EN"
    start_time = time.time()
    result = answer_question(question)
    try:
        response_text_qa = requests.post("http://0.0.0.0:{}/answer_question".format(TEXT_QA_PORT), json={"question_raw": [question]})
        response_text_qa.json()
        logger.info("Success!")
        logger.info("The output data is in json format: {}".format(json.dumps(response_text_qa.json())))
        assert True

    except Exception as e:
        logger.info("Fail!")
        logger.info("The output does not have json format.")
        assert False


@allure.description("""Test response without question""")
@pytest.mark.parametrize(
    "question, gold_result",
    [
        (
            "The weather's so nice today.",
            "",
        ),
    ]
)
def test_text_qa_not_a_question(question, gold_result):
    result = requests.post("http://0.0.0.0:{}/answer_question".format(TEXT_QA_PORT), json={"question_raw": [question]}).json()[0]
    logger.info("Output for a non-question: {}".format(result))
    if result["answer"] == gold_result:
        logger.info("Success!")
        logger.info("Response to a non-question is empty.")
    assert result["answer"] == gold_result


@allure.description("""Test text-qa execution time""")
@pytest.mark.parametrize(
    "question, gold_result",
    [
        (
            "Who was the first man in space?",
            "Yuri Gagarin",
        ),
    ]
)
def test_text_qa_exec_time(question, gold_result):
    start_time = time.time()
    response_factoid = requests.post("http://0.0.0.0:{}/model".format(FACT_CLS_PORT), json={"sentences": [question]}).json()
    exec_time_cls = time.time() - start_time

    start_time = time.time()
    response_fact_retrieval = requests.post("http://0.0.0.0:{}/model".format(FACT_RETRIEVAL_PORT), json={"human_sentences": [question]})
    exec_time_fact_retrieval = time.time() - start_time

    start_time = time.time()
    response_text_qa = requests.post("http://0.0.0.0:{}/model".format(TEXT_QA_PORT), json={"question_raw": question, "top_facts": response_fact_retrieval.json()})
    exec_time_text_qa = time.time() - start_time

    logger.info("Factoid classification execution time: {} seconds".format(exec_time_cls))
    logger.info("Question answering execution time: {} seconds".format(exec_time_text_qa))

    if exec_time_cls <= 0.4 and exec_time_text_qa <= 0.4:
        logger.info("Success!")
    else:
        logger.info("Fail!")
    assert exec_time_cls <= 0.4 and exec_time_text_qa <= 0.4


@allure.description("""Test text-qa deterministic answers""")
@pytest.mark.parametrize(
    "question, gold_result",
    [
        (
            "Who was the first man in space?",
            "Yuri Gagarin",
        ),
    ]
)
def test_text_qa_deterministic(question, gold_result):

    result_1 = requests.post("http://0.0.0.0:{}/answer_question".format(TEXT_QA_PORT), json={"question_raw": [question]}).json()[0]
    logger.info("Input question: {}".format(question))
    logger.info("Answer: {}".format(result_1))

    result_2 = requests.post("http://0.0.0.0:{}/answer_question".format(TEXT_QA_PORT), json={"question_raw": [question]}).json()[0]
    logger.info("Input question: {}".format(question))
    logger.info("Answer: {}".format(result_2))

    if result_1["answer"] == result_2["answer"]:
        logger.info("Success!")
        logger.info("The question answering system is deterministic.")

    assert result_1 == result_2


@allure.description("""Test quality""")
def test_text_qa_quality():
    answers = []
    data = []
    with open('tests/NQ-open.dev.jsonl') as f:
        for line in f:
            data.append(json.loads(line))
    
    logger.info("Evaluating the system on natural question dataset...")
    for i in tqdm(range(len(data)), total=len(data), file=sys.stderr):
        
        sample = data[i]
        ans = answer_question(question=sample['question'], check_factoid=False)[0][0]
        answers.append(ans)
        if i > 0 and i % 300 == 0:
            gold_answers = [sample['answer'] for sample in data[:i]]
            exact_match = squad_v1_exact_match(gold_answers, answers)
            f1 = squad_v1_f1(gold_answers, answers)
            logger.info("EM on {} samples: {}".format(i, exact_match))
            logger.info("F1 on {} samples: {}".format(i, f1))
            logger.info("{}th question: {}".format(i, sample['question']))
            logger.info("{}th gold answers: {}".format(i, sample['answer']))
            logger.info("{}th answer: {}".format(i, ans))


    gold_answers = [sample['answer'] for sample in data]
    exact_match = squad_v1_exact_match(gold_answers, answers)
    f1 = squad_v1_f1(gold_answers, answers)

    if exact_match >= 0.39 and f1 >= 0.46:
        logger.info("Success!")
        logger.info("Exact match: {}".format(exact_match))
        logger.info("F1: {}".format(f1))

    else:
        logger.info("Fail!")
        logger.info("Exact match: {}".format(exact_match))
        logger.info("F1: {}".format(f1))


    assert exact_match >= 0.39 and f1 >= 0.46