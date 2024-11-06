import os
import requests
import logging

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

app = FastAPI()

GIGACHAT_API_URL = os.getenv("GIGACHAT_API_URL", "http://gigachat-api:8187/respond")

class TextInput(BaseModel):
    text: List[str]

@app.post("/translate") # last_human_annotated_utterance
def translate_text(input: TextInput):
    data = {
        "dialog_contexts": [input.text],
        "prompts": ["You are a translator that translates English text into German."],
        "configs": [None],
        "gigachat_credentials": [os.getenv("GIGACHAT_CREDENTIAL")],
        "gigachat_scopes": [os.getenv("GIGACHAT_SCOPE")],
    }
    try:
        response = requests.post(GIGACHAT_API_URL, json=data)
        response.raise_for_status()
        result = response.json()
        logging.info(f"Translated text: {result}")
        translated_text = result[0][0]
        return {"translated_text": translated_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
