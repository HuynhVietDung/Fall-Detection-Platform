import cv2
import time
import os
import math
from datetime import datetime, timedelta
import tensorflow as tf
from tensorflow import keras


class VideoRecorder:
    #  Read and save realtime data from camera.
    def __init__(self, output_path: str, fall_path: str, camera_idx: int = 0,
                 video_duration: int = 10, overlap_time: int = 3) -> None:
        self.video_capture: cv2.VideoCapture = cv2.VideoCapture(camera_idx)
        self.frame_width: int = int(
            self.video_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height: int = int(
            self.video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fourcc: cv2.Videowriter_fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.output_path: str = output_path
        self.fall_path: str = fall_path
        self.video_duration: int = video_duration
        self.overlap_time: int = overlap_time  # Overlap time of each two video
        self.fps: int = self.set_fps()  # Frames per second
        self.total_frames = int(self.video_duration * self.fps)
        self.overlap_frames = int(overlap_time * self.fps)
        model_directory = os.path.join("model", '2303_model.h5')
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

        writers = []
        frame_count = 0

        isFall = 0
        saved_frames = []
        fall_writer = None

        while True:
            ret, frame = self.video_capture.read()
            if not ret:
                break
            previousIsFall = isFall
            isFall = self.checkFall(frame)
            if isFall:
                saved_frames.append(frame)
                if not previousIsFall:
                    start_fall = datetime.now()

            if not isFall:
                if len(saved_frames) > self.fps*3-2:
                    fall_writer = self._start_video_writer(
                        start_fall, self.fall_path)
                    for saved_frame in saved_frames:
                        fall_writer.write(saved_frame)
                    fall_writer.release()
                    saved_frames = []
                    fall_writer = None

            # Start a new writer when the remaining frames equal the overlap frames
            if frame_count == 0 or frame_count % (self.total_frames - self.overlap_frames) == 0:
                new_writer = self._start_video_writer(datetime.now())
                writers.append((new_writer, frame_count + self.total_frames))

            # Remove writers whose range has ended
            if writers and frame_count >= writers[0][1]:
                writers.pop(0)[0].release()

            # Write the frame to all active writers
            if fall_writer:
                fall_writer.write(frame)
            for w, _ in writers:
                w.write(frame)

            frame_count += 1

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    def create_file_path(self, start_time: datetime, classified_output) -> str:
        """Create file path for video."""
        end_time = start_time + timedelta(seconds=self.video_duration)
        start_timestamp = start_time.strftime("%S-%M-%H-%d-%m-%y")
        end_timestamp = end_time.strftime("%S-%M-%H-%d-%m-%y")
        if not classified_output:
            return os.path.join(self.output_path, f"{start_timestamp}__{end_timestamp}_.mp4")
        else:
            return os.path.join(classified_output, f"{start_timestamp}__{end_timestamp}_.mp4")

    def _start_video_writer(self, start_time: datetime, classified_output=None) -> cv2.VideoWriter:
        """ Create cv2.VideoWriter instance for writing video."""
        file_path = self.create_file_path(start_time, classified_output)
        return cv2.VideoWriter(file_path, self.fourcc, self.fps, (self.frame_width, self.frame_height))

    def cleanup(self) -> None:
        print("Release Resources.")
        self.video_capture.release()
        cv2.destroyAllWindows()

    def checkFall(self, frame):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame = cv2.resize(frame, (32, 32))
        frame = tf.keras.utils.img_to_array(frame)
        frame = tf.expand_dims(frame, 0)
        frame = frame/255.
        detect = self.model.predict(frame, verbose=0)[0]
        label = detect.argmax()
        proba = max(detect)
        if label < 4 and proba > 0.5:
            return 1
        return 0

    def __del__(self) -> None:
        if self.video_capture.isOpened():
            self.cleanup()


if __name__ == "__main__":
    # Create a folder saving collected data
    output_folder = "output_folder"
    os.makedirs(output_folder, exist_ok=True)

    fall_folder = "fall_folder"
    os.makedirs(fall_folder, exist_ok=True)

    recorder = VideoRecorder(output_path=output_folder)
    recorder.start_recording()
