import cv2
import time
import os
import math
from datetime import datetime, timedelta


class VideoRecorder:
    #  Read and save realtime data from camera.
    def __init__(self, output_path: str, camera_idx: int = 0,
                 video_duration: int = 10, overlap_time: int = 7) -> None:
        self.video_capture: cv2.VideoCapture = cv2.VideoCapture(camera_idx)
        self.frame_width: int = int(self.video_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height: int = int(self.video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fourcc: cv2.Videowriter_fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.output_path: str = output_path
        self.video_duration: int = video_duration
        self.overlap_time: int = overlap_time  # Overlap time of each two video
        self.fps: int = self.set_fps()  # Frames per second

    def set_fps(self) -> int:
        """Set fps for camera."""
        try:
            frame_rate = self.video_capture.get(cv2.CAP_PROP_FPS)
            return int(frame_rate)
        except ValueError:
            self.video_capture.set(cv2.CAP_PROP_FPS, 12)  # set default FPS values
            return 12

    def start_recording(self) -> None:
        """Record using multiple VideoWriter method for overlapping."""
        if not self.video_capture.isOpened():  # check for camera is opened
            print("Error: Could not open camera.")
            return

        time.sleep(1)  # wait 1s for start camera

        # Number of Video Writer needed
        n_writers = math.ceil(self.video_duration / (self.video_duration - self.overlap_time))

        # Create time range for each Video Writer
        lower = timedelta(seconds=0)
        upper = timedelta(seconds=self.video_duration)
        step_time = timedelta(seconds=self.video_duration - self.overlap_time)
        time_ranges = [(lower + i * step_time, upper + i * step_time) for i in range(n_writers)]

        # Create Video Writers
        start_time = datetime.now()
        writer_list = [self._start_video_writer(start_time + i * step_time) for i in range(n_writers)]

        # Start Recording
        while True:
            ret, frame = self.video_capture.read()
            if not ret:
                continue

            delta_time = datetime.now() - start_time  # Current time
            for i in range(n_writers):  # loop each time range
                if ((delta_time >= time_ranges[i][0]) and
                        (delta_time <= time_ranges[i][1])):  # check if current time in time range.
                    writer_list[i].write(frame)
                elif delta_time > time_ranges[i][1]:  # if not, update Video Writer and time range.
                    writer_list.pop(i).release()
                    writer_list.insert(i, self._start_video_writer(start_time + n_writers
                                                                   * step_time + time_ranges[i][0]))
                    new_range = (time_ranges[i][0] + n_writers * step_time,
                                 time_ranges[i][1] + n_writers * step_time)
                    time_ranges.pop(i)
                    time_ranges.insert(i, new_range)

            if cv2.waitKey(1) & 0xFF == ord('q'):  # Press 'Q' to stop recording
                for writer in writer_list:
                    writer.release()
                break

    def create_file_path(self, start_time: datetime) -> str:
        """Create file path for video."""
        end_time = start_time + timedelta(seconds=self.video_duration)
        start_timestamp = start_time.strftime("%S-%M-%H-%d-%m-%y")
        end_timestamp = end_time.strftime("%S-%M-%H-%d-%m-%y")
        return os.path.join(self.output_path, f"{start_timestamp}__{end_timestamp}_.mp4")

    def _start_video_writer(self, start_time: datetime) -> cv2.VideoWriter:
        """ Create cv2.VideoWriter instance for writing video."""
        file_path = self.create_file_path(start_time)
        return cv2.VideoWriter(file_path, self.fourcc, self.fps, (self.frame_width, self.frame_height))

    def cleanup(self) -> None:
        print("Release Resources.")
        self.video_capture.release()
        cv2.destroyAllWindows()

    def __del__(self) -> None:
        if self.video_capture.isOpened():
            self.cleanup()


if __name__ == "__main__":
    # Create a folder saving collected data
    output_folder = "output_folder"
    os.makedirs(output_folder, exist_ok=True)

    recorder = VideoRecorder(output_path=output_folder)
    recorder.start_recording()
