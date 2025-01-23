FROM tensorflow/tensorflow:1.15.2-gpu

RUN rm -r /etc/apt/sources.list.d/ && \
    apt-get -y update && \
    apt-get install -y \
    build-essential \
    zlib1g-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    wget \
    llvm \
    libncurses5-dev \
    libncursesw5-dev  \
    xz-utils \
    libffi-dev \
    liblzma-dev \
    software-properties-common \
    git \
    sqlite3

ARG LANGUAGE=EN
ENV LANGUAGE ${LANGUAGE}

ARG CONFIG
ARG SERVICE_PORT
ARG SRC_DIR
ARG SED_ARG=" | "

ENV CONFIG=$CONFIG
ENV SERVICE_PORT=$SERVICE_PORT

WORKDIR /src

COPY ./annotators/entity_linking/requirements.txt /src/requirements.txt

COPY ./$SRC_DIR/$CONFIG /src/$CONFIG

RUN pip install --upgrade pip && pip install -r /src/requirements.txt && \
    python -m deeppavlov install $CONFIG

COPY $SRC_DIR /src

RUN sed -i "s|$SED_ARG|g" "$CONFIG"

CMD gunicorn  --workers=1 --timeout 500 server:app -b 0.0.0.0:8075
