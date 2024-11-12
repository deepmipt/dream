FROM python:3.7

# Set the working directory
WORKDIR /src

# Set environment variables for service
ARG SERVICE_PORT
ENV SERVICE_PORT ${SERVICE_PORT}

ARG SERVICE_NAME
ENV SERVICE_NAME ${SERVICE_NAME}

RUN python -m pip install --upgrade pip

COPY ./requirements.txt /src/requirements.txt
COPY ./server.py /src/server.py
COPY ./tests /src/tests
COPY ./test.py /src/test.py
COPY ./bleu_metric_test.py /src/bleu_metric_test.py

RUN mkdir -p /src/aux_files/AudioCaption/
RUN wget --no-check-certificate -O /src/aux_files/AudioCaption/experiments.zip https://files.deeppavlov.ai/dolidze/for_voice_service/AudioCaption.zip
RUN unzip /src/aux_files/AudioCaption/experiments.zip -d /src
RUN ls /src

RUN apt update
RUN apt install -y gcc libsndfile1-dev ffmpeg

RUN python -m pip install -r requirements.txt
RUN pip install -r /src/AudioCaption/requirements.txt

RUN python -m pip install numba==0.48
RUN python -m pip install resampy==0.3.1
RUN python -m pip install torchaudio==0.9.1
RUN python -m pip install torchlibrosa==0.0.9
RUN pip install sndfile

# Create directory for pretrained models and download them
RUN mkdir -p pretrained_feature_extractors
RUN wget https://github.com/wsntxxn/AudioCaption/releases/download/v0.0.2/contrastive_pretrain_cnn14_bertm.pth -O pretrained_feature_extractors/contrastive_pretrain_cnn14_bertm.pth
RUN wget https://github.com/wsntxxn/AudioCaption/releases/download/v0.0.2/audiocaps_cntrstv_cnn14rnn_trm.zip -O audiocaps_cntrstv_cnn14rnn_trm.zip
RUN unzip audiocaps_cntrstv_cnn14rnn_trm.zip -d pretrained_feature_extractors
RUN wget https://github.com/deeppavlov/AudioCaptionBKP/releases/download/bkp/clotho_cntrstv_cnn14rnn_trm.zip
RUN unzip clotho_cntrstv_cnn14rnn_trm.zip
RUN mv clotho_cntrstv_cnn14rnn_trm AudioCaption

RUN pip install -e /src/AudioCaption
RUN mkdir -p audio_input
RUN wget "https://raw.githubusercontent.com/deeppavlov/mmodal_files_bkp/refs/heads/main/rain.wav" -O audio_input/rain.wav
RUN wget "https://raw.githubusercontent.com/deeppavlov/mmodal_files_bkp/refs/heads/main/rain.mp3" -O audio_input/rain.mp3

RUN wget "https://lnsigo.mipt.ru/export/serikov/mmodal-ac/clotho_subset/00_BRUSH.mp3" -O audio_input/00_BRUSH.mp3
RUN wget "https://lnsigo.mipt.ru/export/serikov/mmodal-ac/clotho_subset/01-BikeDemo_Speaker.mp3" -O audio_input/01-BikeDemo_Speaker.mp3
RUN wget "https://lnsigo.mipt.ru/export/serikov/mmodal-ac/clotho_subset/002_78_rpm_vinyl_noise_44_16_lossless.mp3" -O audio_input/002_78_rpm_vinyl_noise_44_16_lossless.mp3
RUN wget "https://lnsigo.mipt.ru/export/serikov/mmodal-ac/clotho_subset/00264%20hill%20creek%201.mp3" -O audio_input/00264%20hill%20creek%201.mp3
RUN wget "https://lnsigo.mipt.ru/export/serikov/mmodal-ac/clotho_subset/department.store.mp3" -O audio_input/department.store.mp3
RUN wget "https://lnsigo.mipt.ru/export/serikov/mmodal-ac/clotho_subset/mosquito.mp3" -O audio_input/mosquito.mp3
RUN wget "https://lnsigo.mipt.ru/export/serikov/mmodal-ac/clotho_subset/smeared%20bell.mp3" -O audio_input/smeared%20bell.mp3
RUN wget "https://lnsigo.mipt.ru/export/serikov/mmodal-ac/clotho_subset/street_corner.mp3" -O audio_input/street_corner.mp3
RUN wget "https://lnsigo.mipt.ru/export/serikov/mmodal-ac/clotho_subset/Water%20Sound.mp3" -O audio_input/Water%20Sound.mp3
RUN wget "https://lnsigo.mipt.ru/export/serikov/mmodal-ac/clotho_subset/Whining%20Dog.mp3" -O audio_input/Whining%20Dog.mp3