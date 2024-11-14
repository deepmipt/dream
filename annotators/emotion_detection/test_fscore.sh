
mkdir /test
wget -O testdata http://files.deeppavlov.ai/dream_data/emotion_detection/meld_testdata.tar.gz && tar -xf testdata -C /test/
python3 test_emotion_detection_fscore.py