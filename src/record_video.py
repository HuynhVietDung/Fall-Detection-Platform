from datetime import datetime, timedelta
from model_inference import ModelInference
from ipfs_transfer import IPFSTransfer
import cv2
import os
import random
import time
import argparse

# Paste IPFS Gateway link and API Key here
public_link = ""
api_key = ""
secret_key = ""    

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

        # Create a folder saving collected data
        os.makedirs(self.output_folder, exist_ok=True)
        os.makedirs(self.result_folder, exist_ok=True)

    def set_fps(self) -> int:
        """Set fps for camera."""
        try:
            return int(self.video_capture.get(cv2.CAP_PROP_FPS))
        except ValueError:
            self.video_capture.set(cv2.CAP_PROP_FPS, 12)  # set default FPS values
            return 12

    def start_recording(self) -> None:
        """Record using VideoWriter."""
        if not self.video_capture.isOpened():  # check for camera is opened
            raise Exception("Error: Could not open camera.")

        time.sleep(1)  # wait 1s for start camera

        # Initialize variables
        file_name = None
        frame_count = 0
        isFall = False
        start_time = -1
        end_time = -1
        model = ModelInference(os.path.join("model", "2303_model.h5"))
        ipfs_transfer = IPFSTransfer(public_link, api_key, secret_key)

        while True:
            ret, frame = self.video_capture.read()
            if not ret:
                break

            str_time = datetime.now()
            previousIsFall = isFall
            isFall = model.inference(frame)

            if isFall and not previousIsFall:
                start_time = int(frame_count / self.fps)

            if not isFall and start_time != -1:
                end_time = int(frame_count / self.fps)
                if end_time - start_time > 2:
                    writer.release()
                    frame_count = 0
                    cid = ipfs_transfer.upload_video(file_name, api_key, secret_key)
                    video_url = ipfs_transfer.get_url(cid, file_name)
                    self.make_txt(file_name, video_url, start_time, end_time)
                    print("Time: ", (datetime.now() - start_time).seconds)
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
                file_name = self.create_file_path(timenow)

            # Remove writers whose range has ended
            if frame_count >= self.total_frames:
                writer.release()
                frame_count = -1
            else:
                writer.write(frame)

            frame_count += 1

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    
    def make_txt(self, file_name: str, video_url: str, start_time: str, end_time: str) -> None:
        file_name = os.path.relpath(file_name, self.output_path).replace(".mp4", "")
        with open(os.path.join(self.result_path, f"{file_name}.txt"), "w") as f:
            f.write(f"{video_url} - {start_time} - {end_time}\n")

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

    def __del__(self) -> None:
        if self.video_capture.isOpened():
            self.cleanup()


if __name__ == "__main__":
    # Initialize the parser
    parser = argparse.ArgumentParser(description="Process a file with path and index.")

    # Add arguments for path and index
    parser.add_argument("vid_dir", type=str, help="Directoy of video files.")
    parser.add_argument("txt_dir", type=str, help="Directoy of txt files.")
    parser.add_argument("idx", type=int, help="Index value of camera.")

    # Parse the arguments
    args = parser.parse_args()
    output_folder, result_folder, camera_idx = args.vid_dir, args.txt_dir, args.idx

    # Stat video streaming
    recorder = VideoRecorder(output_path=output_folder, camera_idx=camera_idx, result_path=result_folder)
    recorder.start_recording()

