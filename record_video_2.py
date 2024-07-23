import cv2
import time
import os
from datetime import datetime, timedelta
import tensorflow as tf
from tensorflow import keras
from requests import Session, Request
import string
import random

public_link = "https://jade-managing-damselfly-241.mypinata.cloud/ipfs/"
secret_key = "7ec381f913be80dcdc3ec4b2a7f85efe30164f0fa90dcd2269d45bcfeef6de1b"


def upload_video(filename):
    # time.sleep(1)
    ipfs_url = "https://api.pinata.cloud/pinning/pinFileToIPFS"
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.146 Safari/537.36",
        "pinata_api_key": "6b14f6032330663fcd57",
        "pinata_secret_api_key": secret_key,
    }
    files = [("file", (filename, open(filename, "rb")))]
    request = Request("POST", ipfs_url, headers=headers, files=files).prepare()
    response = Session().send(request)
    return response.json().get("IpfsHash")


class VideoRecorder:
    #  Read and save realtime data from camera.
    def __init__(
        self,
        output_path: str,
        result_path: str,
        camera_idx: int = 0,
        video_duration: int = 10,
        overlap_time: int = 0,
    ) -> None:
        self.video_capture: cv2.VideoCapture = cv2.VideoCapture(camera_idx)
        self.frame_width: int = int(self.video_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height: int = int(self.video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fourcc: cv2.Videowriter_fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        self.output_path: str = output_path
        self.result_path: str = result_path
        self.video_duration: int = video_duration
        self.overlap_time: int = overlap_time  # Overlap time of each two video
        self.fps: int = self.set_fps()  # Frames per second
        self.total_frames = int(self.video_duration * self.fps)
        self.overlap_frames = int(overlap_time * self.fps)
        model_directory = os.path.join("model", "2403_model.h5")
        self.model = keras.models.load_model(model_directory, compile=False)

    def set_fps(self) -> int:
        """Set fps for camera."""
        try:
            frame_rate = self.video_capture.get(cv2.CAP_PROP_FPS)
            return int(frame_rate)
        except ValueError:
            # set default FPS values
            self.video_capture.set(cv2.CAP_PROP_FPS, 12)
            return 12

    def start_recording(self) -> None:
        """Record using multiple VideoWriter method for overlapping."""
        if not self.video_capture.isOpened():  # check for camera is opened
            print("Error: Could not open camera.")
            return

        time.sleep(1)  # wait 1s for start camera

        filename = None
        frame_count = 0

        isFall = 0
        start_time = -1
        end_time = -1

        while True:
            ret, frame = self.video_capture.read()
            if not ret:
                break
            previousIsFall = isFall
            isFall = self.checkFall(frame)
            if isFall:
                if not previousIsFall:
                    start_time = int(frame_count / self.fps)

            if not isFall and start_time != -1:
                end_time = int(frame_count / self.fps)
                if end_time - start_time > 2:
                    writer.release()
                    frame_count = 0
                    hash_id = upload_video(filename)
                    video_url = os.path.join(public_link, hash_id)
                    video_url = os.path.join(video_url, filename)
                    filename = os.path.relpath(filename, self.output_path)
                    filename = filename.replace(".mp4", "")

                    f = open(os.path.join(self.result_path, f"{filename}.txt"), "w")
                    f.write(f"{video_url} - {start_time} - {end_time}\n")
                    f.close()

                else:
                    end_time = -1
                start_time = -1

            # Start a new writer when the remaining frames equal the overlap frames
            if (
                frame_count == 0
                or frame_count % (self.total_frames - self.overlap_frames) == 0
            ):
                timenow = datetime.now()
                writer = self._start_video_writer(timenow)
                filename = self.create_file_path(timenow)

            # Remove writers whose range has ended
            if frame_count >= self.total_frames:
                writer.release()
                frame_count = -1
            else:
                writer.write(frame)

            frame_count += 1

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    def create_file_path(self, start_time: datetime) -> str:
        """Create file path for video."""
        end_time = start_time + timedelta(seconds=self.video_duration)
        start_timestamp = start_time.strftime("%S-%M-%H-%d-%m-%y")
        end_timestamp = end_time.strftime("%S-%M-%H-%d-%m-%y")
        return os.path.join(
            self.output_path, f"{start_timestamp}__{end_timestamp}_.mp4"
        )

    def _start_video_writer(
        self, start_time: datetime, classified_output=None
    ) -> cv2.VideoWriter:
        """Create cv2.VideoWriter instance for writing video."""
        file_path = self.create_file_path(start_time)
        return cv2.VideoWriter(
            file_path, self.fourcc, self.fps, (self.frame_width, self.frame_height)
        )

    def cleanup(self) -> None:
        print("Release Resources.")
        self.video_capture.release()
        cv2.destroyAllWindows()

    def checkFall(self, frame):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame = cv2.resize(frame, (32, 32))
        frame = tf.keras.utils.img_to_array(frame)
        frame = tf.expand_dims(frame, 0)
        frame = frame / 255.0
        detect = self.model.predict(frame, verbose=0)[0]
        label = detect.argmax()
        proba = max(detect)
        if label < 4 and proba > 0.6:
            return 1
        return 0

    def __del__(self) -> None:
        if self.video_capture.isOpened():
            self.cleanup()


if __name__ == "__main__":
    # Create a folder saving collected data
    output_folder = "output_folder"
    os.makedirs(output_folder, exist_ok=True)

    result_folder = "result_folder_1"
    os.makedirs(result_folder, exist_ok=True)

    recorder = VideoRecorder(
        camera_idx=1, output_path=output_folder, result_path=result_folder
    )
    recorder.start_recording()
