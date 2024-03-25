import os
import threading
from record_video import VideoRecorder
from typing import List
import glob
import shutil
import time
from tensorflow import keras
import cv2
import tensorflow as tf
from multiprocessing import Process

model_directory = os.path.join("model", '2303_model.h5')
model = keras.models.load_model(model_directory, compile=False)

def max_consecutive_true(input_list):
    max_length = 0
    current_length = 0

    for value in input_list:
        if value:
            # If the value is True, increase the current length
            current_length += 1
            # Update the max length if the current length is greater
            max_length = max(max_length, current_length)
        else:
            # Reset the current length if the value is False
            current_length = 0

    return max_length

def detect_fall_each_video(video_path):
  vid = cv2.VideoCapture(video_path)
  success, frame = vid.read()
  if not success:
      return -1
  isFall = 0
  fallCount = 0
  fallDetectFrames = []
  while success:
      try:
          frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
      except:
          return -1
      frame = cv2.resize(frame, (32, 32))
      frame = tf.keras.utils.img_to_array(frame)
      frame = tf.expand_dims(frame, 0)
      detect = model.predict(frame, verbose=0).argmax()
      fallDetectFrames.append(detect)
      if detect:
        fallCount+=1
        if fallCount>12 and max_consecutive_true(fallDetectFrames)>6:
          isFall = 1
          break
      success, frame = vid.read()
  return isFall


def get_video_paths(output_folder):
    video_paths = []
    video_patterns = ['*.mp4', '*.avi', '*.mov']
    for root, dirs, files in os.walk(output_folder):
        for pattern in video_patterns:
            for filename in glob.glob(os.path.join(root, pattern)):
                video_paths.append(filename)
    video_paths.sort(key=lambda x: os.path.getctime(x))
    return video_paths


def detect_fall(output_folder: str, classified_folder: str):
    call_times = 0
    while True:
        videos_paths = get_video_paths(output_folder)
        if len(videos_paths) == 0:
            time.sleep(10)
            call_times += 1
            if call_times == 10:  # Call this function 10 times but no videos
                break
        else:
            call_times = 0
            for video_path in videos_paths:
                new_video_path = os.path.relpath(video_path, output_folder)
                new_video_path = new_video_path.replace(
                    " ", "").replace("/", "-")
                isFall = detect_fall_each_video(video_path)
                if isFall == -1:
                    continue
                if isFall:
                    new_video_path = os.path.join(
                        classified_folder, "label_1", new_video_path)
                    shutil.move(video_path, new_video_path)
                else:
                    new_video_path = os.path.join(
                        classified_folder, "label_0", new_video_path)
                    shutil.move(video_path, new_video_path)


def create_folders(out_folder: str, number_of_sub_folder: int = 0) -> List[str]:
    # Create the output folder if it doesn't exist
    os.makedirs(out_folder, exist_ok=True)

    path_list: List = []
    # Create sub folders
    for i in range(number_of_sub_folder):
        path = os.path.join(out_folder, f"Camera {i + 1}")
        path_list.append(path)
        os.makedirs(path,  exist_ok=True)
    return path_list


if __name__ == "__main__":
    output_folder = "output_folder"
    camera_ids = [0, 1]
    n_camera = 2
    video_duration = 10
    overlap_time = 7

    # Create output folder for each camera.
    output_folder_list = create_folders(
        output_folder, number_of_sub_folder=n_camera)

    # Create output for model
    classified_folder = "classified_folder"
    os.makedirs(classified_folder, exist_ok=True)
    os.makedirs(os.path.join(classified_folder, "label_0"), exist_ok=True)
    os.makedirs(os.path.join(classified_folder, "label_1"), exist_ok=True)

    # Create Video Writers.
    video_recorder_list = [VideoRecorder(camera_idx=camera_ids[i], output_path=output_folder_list[i],
                                         video_duration=video_duration, overlap_time=overlap_time)
                           for i in range(n_camera)]
    # Create Threads.
    thread_list = [threading.Thread(target=video_recorder_list[i].start_recording)
                   for i in range(n_camera)]
    # Start Running.
    for thread in thread_list:
        thread.start()
    classify_process = Process(target=detect_fall, args=(
        output_folder, classified_folder))
    classify_process.start()
    # Stop.
    for thread in thread_list:
        thread.join()
    classify_process.join()
