FROM python:3.9

WORKDIR /src
RUN mkdir -p /data

RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

RUN pip install gdown

RUN gdown --id 13fs86zfN7Jstgyv38AeKPiq-RYpsYy3- -O /data/extraversion_tae898_emoberta-base_seed-42.pt
RUN gdown --id 1VSvjFRhqCBr38NI1QHlU9Qh2iMfXUAK6 -O /data/neuroticism_tae898_emoberta-base_seed-42.pt
RUN gdown --id 1DOUBsK-r0_dy3m9hPBNjkCbzKrUaKaSi -O /data/agreeableness_tae898_emoberta-base_seed-42.pt
RUN gdown --id 1LFEOHafz7imihMNhJCwdVBIqk6PtliS5 -O /data/conscientiousness_tae898_emoberta-base_seed-42.pt
RUN gdown --id 18C3IfiXKGVgYmqi8kTjEpKqp9kWisA4_ -O /data/openness_tae898_emoberta-base_seed-42.pt
RUN mkdir -p /data/baseline-essays
RUN gdown --id 17BDVVeq6rTqBRZQIlDIndU852_4flFtc -O /data/baseline-essays/essays_test.csv

COPY requirements.txt ./requirements.txt

RUN pip install -r requirements.txt

COPY . /src

CMD ["uvicorn", "server:app", "--reload", "--port", "8026"]
