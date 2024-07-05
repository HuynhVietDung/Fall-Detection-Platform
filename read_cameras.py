import os
import threading
from record_video import VideoRecorder
from typing import List


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
    result_folder = "result_folder"
    os.makedirs(result_folder, exist_ok=True)

    output_folder = "output_folder"
    camera_ids = [0, 1]
    n_camera = 2
    video_duration = 10
    overlap_time = 0

    # Create output folder for each camera.
    output_folder_list = create_folders(
        output_folder, number_of_sub_folder=n_camera)

    # Create Video Writers.
    video_recorder_list = [VideoRecorder(camera_idx=camera_ids[i], output_path=output_folder_list[i],
                                         result_path=result_folder,
                                         video_duration=video_duration, overlap_time=overlap_time)
                           for i in range(n_camera)]
    # Create Threads.
    thread_list = [threading.Thread(target=video_recorder_list[i].start_recording)
                   for i in range(n_camera)]

    # Start Running.
    for thread in thread_list:
        thread.start()
    # Stop.
    for thread in thread_list:
        thread.join()
