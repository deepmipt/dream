# syntax=docker/dockerfile:experimental

FROM pytorch/pytorch:1.12.1-cuda11.3-cudnn8-runtime

WORKDIR /src

ARG PRETRAINED_MODEL_NAME_OR_PATH 
ENV PRETRAINED_MODEL_NAME_OR_PATH ${PRETRAINED_MODEL_NAME_OR_PATH}
ARG SERVICE_PORT
ENV SERVICE_PORT ${SERVICE_PORT}

RUN mkdir /data/

COPY ./requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

COPY . /src

RUN python3 -c "from transformers import AutoModel, AutoTokenizer; AutoTokenizer.from_pretrained('${PRETRAINED_MODEL_NAME_OR_PATH}'); AutoModel.from_pretrained('${PRETRAINED_MODEL_NAME_OR_PATH}')"


CMD gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT} --timeout=1200

