import os
import logging
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

from gigachat import GigaChat
from gigachat.models import Chat

app = FastAPI()

class TextInput(BaseModel):
    sentences: List[str]

if not all([os.getenv("GIGACHAT_CREDENTIAL"), os.getenv("GIGACHAT_SCOPE")]):
    logging.error("ENV VARIABLES FOR GIGACHAT ARE NOT SET, THE SERVICE WILL NOT WORK")

@app.post("/translate")
def translate_text(payload: TextInput):
    gigachat_api_key = os.getenv("GIGACHAT_CREDENTIAL")
    gigachat_org = os.getenv("GIGACHAT_SCOPE")

    if not all([gigachat_api_key, gigachat_org]):
        logging.error("Gigachat credentials are not set")
        raise HTTPException(status_code=500, detail="Gigachat credentials are not set")

    translated_text = []

    for msg in payload.sentences:
        try:
            giga = GigaChat(credentials=gigachat_api_key, verify_ssl_certs=False)

            messages = [
                {
                    "role": "system",
                    "content": "You are a translator that translates English text into German."
                },
                {
                    "role": "user",
                    "content": msg
                }
            ]

            payload = Chat(messages=messages, scope=gigachat_org)

            response = giga.chat(payload)

            translated_text += [response.choices[0].message.content.strip()]
            logging.info(f"Translated text: {translated_text}")
        except Exception as e:
            logging.exception("Error during translation")
            raise HTTPException(status_code=500, detail=str(e))
    return jsonable_encoder([{"batch": translated_text}])
