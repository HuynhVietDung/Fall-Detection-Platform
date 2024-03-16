import os
import threading
from record_video import VideoRecorder


if __name__ == '__main__':

    output_folder = "output_folder"
    sub_folder1 = "Camera 1"
    sub_folder2 = "Camera 2"

    c1_path = os.path.join(output_folder, sub_folder1)
    c2_path = os.path.join(output_folder, sub_folder2)

    os.makedirs(output_folder, exist_ok=True)
    os.makedirs(c1_path, exist_ok=True)
    os.makedirs(c2_path, exist_ok=True)

    #
    recorder1 = VideoRecorder(output_path=c1_path, camera_idx=0)
    recorder2 = VideoRecorder(output_path=c2_path, camera_idx=1)

    #
    c1_thread = threading.Thread(target=recorder1.start_recording)  # Camera 1
    c2_thread = threading.Thread(target=recorder2.start_recording)  # Camera 2

    #
    c1_thread.start()
    c2_thread.start()

    # Finish
    c1_thread.join()
    c2_thread.join()
