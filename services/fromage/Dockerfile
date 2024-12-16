# syntax=docker/dockerfile:experimental
FROM pytorch/pytorch:1.5-cuda10.1-cudnn7-runtime

WORKDIR /src

ARG SERVICE_PORT
ENV SERVICE_PORT ${SERVICE_PORT}

ARG SERVICE_NAME
ENV SERVICE_NAME ${SERVICE_NAME}

RUN python -m pip install --upgrade pip
RUN apt-get update && apt-get install -y wget

# ENV PYTHONPATH "/src/fromage:/fromage:$PYTHONPATH"

COPY ./services/fromage/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt
RUN pip install --upgrade transformers
# RUN mkdir -p /services/fromage

COPY ./services/fromage/ /src/
# COPY ./common/ ./common/
ENV PYTHONPATH="/src:$PYTHONPATH"