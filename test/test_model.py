import cv2
import time
import os
from datetime import datetime, timedelta
import tensorflow as tf
from tensorflow import keras
from requests import Session, Request
import string
import random


def frame_predict(frame):
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    frame = cv2.resize(frame, (32, 32))
    frame = tf.keras.utils.img_to_array(frame)
    frame = tf.expand_dims(frame, 0)
    frame = frame / 255.0
    detect = detection_model.predict(frame, verbose=0)[0]
    label = detect.argmax()
    proba = max(detect)
    if label < 4 and proba > 0.5:
        return 1
    return 0


def video_predict(video_path):
    vid = cv2.VideoCapture(video_path)

    success = True
    start = -1
    end = -1
    count = 0
    previous = False
    while success:
        success, frame = vid.read()
        if not success:
            break
        guess = frame_predict(frame)
        if guess:
            if not previous:
                start = int(count / 12)
        else:
            if previous:
                end = int(count / 12)
        if start != -1 and end - start > 2:
            return 1
        count += 1
    return 0


detection_model = keras.models.load_model("model/2403_model.h5", compile=False)


video_paths = os.listdir("output_folder")
if video_paths:
    for path in video_paths:
        start_time = datetime.now()
        video_path = "output_folder/" + path
        print(video_path)
        print(video_predict(video_path))
        print((datetime.now() - start_time).seconds)
