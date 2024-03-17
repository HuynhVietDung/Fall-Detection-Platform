import cv2
import time
import os
import shutil
from typing import List, Optional
from datetime import datetime, timedelta


class CameraCapture:
    """Captures video from multiple cameras and saves them with overlaps."""

    def __init__(self, camera_ids: List[int], output_path: str, video_duration: int, overlap_duration: int):
        self.camera_ids = camera_ids
        self.output_path = output_path
        self.video_duration = video_duration  # Duration of each video in seconds
        self.overlap_duration = overlap_duration  # Overlap between videos in seconds
        self.video_captures: List[cv2.VideoCapture] = []

        # Initialize VideoCapture objects
        for cam_id in self.camera_ids:
            cap = cv2.VideoCapture(cam_id)
            if not cap.isOpened():
                print(f"Error: Could not open camera {cam_id}")
            else:
                self.video_captures.append(cap)

    def start_recording(self) -> None:
        if not self.video_captures:  # Check if any cameras are initialized
            print("Error: No cameras found.")
            return

        # Calculate recording parameters
        self.fps = self._get_fps()
        self.frames_per_video = int(self.video_duration * self.fps)
        self.frames_per_overlap = int(self.overlap_duration * self.fps)

        # Create output folder if not exist
        os.makedirs(self.output_path, exist_ok=True)

        video_id = 0
        start_time = datetime.now()  # Record initial start time

        while True:
            for i, vid_cap in enumerate(self.video_captures):
                out = self._start_video_writer(video_id, i, start_time)
                self._record_video(vid_cap, out, self.frames_per_video)
                out.release()
                video_id += 1

            # Update start time for the next video segment
            start_time += timedelta(seconds=self.video_duration - self.overlap_duration)

            # Introduce overlap delay only if necessary
            if self.overlap_duration > 0:
                time.sleep(self.overlap_duration)

    def _get_fps(self) -> int:
        """Tries to get FPS from the first camera, otherwise sets default to 20"""
        if self.video_captures:
            try:
                fps = self.video_captures[0].get(cv2.CAP_PROP_FPS)
                return int(fps)
            except ValueError:
                pass  # Fallback to default
        return 20  # Default FPS

    def _start_video_writer(self, video_id: int, camera_id: int, start_time: datetime):
        end_time = start_time + timedelta(seconds=self.video_duration)
        start_timestamp = start_time.strftime("%S-%M-%H-%d-%m-%y")
        end_timestamp = end_time.strftime("%S-%M-%H-%d-%m-%y")

        filename = os.path.join(self.output_path, f"{camera_id}__{video_id}__{start_timestamp}__{end_timestamp}_.mp4")
        print(filename)

        # fourcc = cv2.VideoWriter_fourcc(*'XVID')
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # MPEG-4
        width = int(self.video_captures[0].get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.video_captures[0].get(cv2.CAP_PROP_FRAME_HEIGHT))
        return cv2.VideoWriter(filename, fourcc, self.fps, (width, height))

    def _record_video(self, video_capture: cv2.VideoCapture, out: cv2.VideoWriter, frames_to_record: int) -> None:
        """Records video from a specific camera."""
        frame_count = 0
        # Add a log
        print(f"Recording video {frames_to_record} frames from camera {video_capture}")
        while frame_count < frames_to_record:
            ret, frame = video_capture.read()
            if not ret:
                print("Error: Failed to read frame.")
                break

            frame = cv2.flip(frame, 1)  # Flip the frame if needed
            out.write(frame)
            frame_count += 1

    def cleanup(self) -> None:
        print("Releasing resources...")
        for cap in self.video_captures:
            cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    camera_ids = [0]  # List of camera indices
    output_path = "output_videos"

    video_duration = 10  # Seconds
    overlap_duration = 5  # Seconds

    recorder = CameraCapture(camera_ids, output_path,
                             video_duration, overlap_duration)
    try:
        recorder.start_recording()
    except KeyboardInterrupt:  # Catch the keyboard interrupt (Ctrl+C or 'q')
        print("Program stopped by user.")
    finally:
        recorder.cleanup()  # Ensure resources are released
        # Remove the output folder if it exists
        # if os.path.exists(output_path):
        #     shutil.rmtree(output_path)
        #     print("Output folder deleted.")
