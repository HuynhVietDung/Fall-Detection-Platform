import cv2
import time
import os
import math
import logging
from datetime import datetime, timedelta
from moviepy.editor import VideoFileClip, concatenate_videoclips

logging.getLogger().setLevel(logging.CRITICAL)


class VideoRecorder:
    #  Read and save realtime data from camera.

    def __init__(self, output_path: str, camera_idx: int = 0, video_path: str = '',
                 video_duration: int = 10, overlap_time: int = 7) -> None:
        self.cap: cv2.VideoCapture = cv2.VideoCapture(video_path if video_path != '' else camera_idx)
        self.frame_width: int = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height: int = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fourcc: cv2.Videowriter_fourcc = cv2.VideoWriter_fourcc(*'MP4V')
        self.output_path: str = output_path
        self.video_duration: int = video_duration
        self.overlap_time: int = overlap_time  # Overlap time of each two video
        self.is_recording: bool = False
        self.fps: int = self.set_fps()  # Frames per second
        self.start_time: datetime = datetime.now()  # start recording time

    def set_fps(self) -> int:
        """Set fps for camera."""
        try:
            frame_rate = self.cap.get(cv2.CAP_PROP_FPS)
            # print("Number of frames per second: ", int(frame_rate))
            return int(frame_rate)
        except ValueError:
            self.cap.set(cv2.CAP_PROP_FPS, 20)  # set default FPS values
            return 20

    def start_recording_v1(self, chunk_time: int = 20) -> None:
        """Recording root videos (chunks) and cutting root video into overlapping videos."""
        if not self.cap.isOpened():  # check for camera is opened
            print("Error: Could not open camera.")
            return

        time.sleep(1)  # wait 1s for start camera

        self.start_time = datetime.now()
        frame_start = 0
        while True:
            try:
                self.is_recording = True
                file_path = self._record(frame_start=frame_start)  # start recording

                if  not cv2.VideoCapture(file_path).isOpened():
                    break

                self.overlap_video(file_path, self.video_duration, chunk_time)
                os.remove(file_path)

                frame_start += self.fps * chunk_time
                self.start_time += timedelta(seconds=chunk_time)
            except KeyboardInterrupt:
                break

    def start_recording_v2(self) -> None:
        """Recording by using cut and concat 2 videos method for overlapping."""
        if not self.cap.isOpened():  # check for camera is opened
            print("Error: Could not open camera.")
            return

        time.sleep(1)  # wait 1s for start camera
        self.is_recording = True
        self.start_time = datetime.now()
        file_path = self._record(record_time=self.video_duration)

        record_time = self.video_duration - self.overlap_time
        while True:
            try:
                self.start_time = self.start_time + timedelta(seconds=record_time)
                self.is_recording = True
                file_path_2 = self._record(record_time=record_time)
                self.cut_and_concat_two_videos(video1_path=file_path, video2_path=file_path_2,
                                               video1_start= record_time,
                                               video1_end= self.video_duration)
                file_path = file_path_2
            except KeyboardInterrupt:  # Catch the keyboard interrupt (Ctrl+C or 'q')
                break

    def start_recording_v3_1(self) -> None:
        """Record using multiple VideoWriter method and time count method for overlapping."""
        if not self.cap.isOpened():  # check for camera is opened
            print("Error: Could not open camera.")
            return

        time.sleep(1)  # wait 1s for start camera
        self.start_time = datetime.now()
        self.is_recording = True

        lower = timedelta(seconds=0)
        upper = timedelta(seconds=self.video_duration)
        step_time = timedelta(seconds=self.video_duration - self.overlap_time)
        n_writer = math.ceil(self.video_duration / (self.video_duration - self.overlap_time))
        range_list = [(lower + i * step_time, upper + i * step_time) for i in range(n_writer)]
        writer_list = [self._start_video_writer(self.start_time + i * step_time)
                       for i in range(n_writer)]

        # for (l, u) in range_list:
        #    print(f"Range ({l}, {u}).")

        start_time = datetime.now()
        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("Error: Failed to read.")
                break

            delta_time = datetime.now() - start_time
            for idx in range(n_writer):
                if ((delta_time >= range_list[idx][0]) and  ## TODO: The video length is 20s, need to fix.
                        (delta_time <= range_list[idx][1])):
                    writer_list[idx].write(frame)
                if delta_time > range_list[idx][1]:
                    writer_list.pop(idx).release()
                    writer_list.insert(idx, self._start_video_writer(self.start_time + n_writer
                                                                     * step_time + range_list[idx][0]))
                    new_range = (range_list[idx][0] + n_writer * step_time,
                                 range_list[idx][1] + n_writer * step_time)
                    range_list.pop(idx)
                    range_list.insert(idx, new_range)
                    # print(f"Range ({new_range[0]}, {new_range[1]}).")

            if cv2.waitKey(1) & 0xFF == ord('q'):  # Press 'Q' to stop recording
                # print(f'Total runtime: {time.time() - self.start_time}')
                for writer in writer_list:
                    writer.release()
                break

    def start_recording_v3_2(self) -> None:
        """Record using multiple VideoWriter method and frame count method for overlapping."""
        if not self.cap.isOpened():  # check for camera is opened
            print("Error: Could not open camera.")
            return

        time.sleep(1)  # wait 1s for start camera
        self.start_time = datetime.now()
        self.is_recording = True

        lower = 0
        upper = self.video_duration * self.fps
        step = (self.video_duration - self.overlap_time) * self.fps
        step_time = timedelta(seconds=self.video_duration - self.overlap_time)
        n_writer = math.ceil(self.video_duration / (self.video_duration - self.overlap_time))
        range_list = [(lower + i * step, upper + i * step) for i in range(n_writer)]
        writer_list = [self._start_video_writer(self.start_time + i * step_time)
                       for i in range(n_writer)]

        # for (l, u) in range_list:
        #    print(f"Range ({l}, {u}).")

        frame_count = 0
        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("Error: Failed to read.")
                break

            for idx in range(n_writer):
                if ((frame_count >= range_list[idx][0]) and
                        (frame_count < range_list[idx][1])):
                    writer_list[idx].write(frame)
                if frame_count > range_list[idx][1]:
                    writer_list.pop(idx).release()
                    writer_list.insert(idx, self._start_video_writer(self.start_time + n_writer * step_time
                                                                     + timedelta(seconds=range_list[idx][0] / self.fps))
                                       )
                    new_range = (range_list[idx][0] + n_writer * step, range_list[idx][1] + n_writer * step)
                    range_list.pop(idx)
                    range_list.insert(idx, new_range)
                    # print(f"Range ({new_range[0]}, {new_range[1]}).")

            if cv2.waitKey(1) & 0xFF == ord('q'):  # Press 'Q' to stop recording
                # print(f'Total runtime: {time.time() - self.start_time}')
                for writer in writer_list:
                    writer.release()
                break
            frame_count += 1

    @staticmethod
    def cut_and_concat_two_videos(video1_path: str, video2_path: str, video1_start: int,
                                  video1_end: int) -> None:
        """Cut video1 and concat with video2. This function is used for self.start_recording_v2."""
        clip1 = VideoFileClip(video1_path).subclip(video1_start, video1_end)
        clip2 = VideoFileClip(video2_path)
        final_clip = concatenate_videoclips([clip1, clip2])
        os.remove(video2_path)
        final_clip.write_videofile(video2_path)

    def _record(self, record_time: int = 20, frame_start: int = 0) -> str:
        """
            Record from specific frame and using frame count method.
           Used for self.start_recording_v1 and self.recording_v2.
        """
        file_path = self.create_file_path(self.start_time)
        writer = self._start_video_writer(self.start_time, file_path)
        print("Running.....")

        frame_count = 0
        frame_to_read = record_time * self.fps  # Total frame needed to read
        if frame_start != 0:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_start)  # Set the start frame

        while self.is_recording and (frame_count <= frame_to_read):
            ret, frame = self.cap.read()
            if not ret:
                print("Error: Failed to read.")
                break

            # frame = cv2.flip(frame, 1)
            writer.write(frame)
            # cv2.imshow("Camera Feed", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):  # Press 'Q' to stop recording
                # print(f'Total runtime: {time.time() - self.start_time}')
                break
            frame_count += 1

        self.stop_recording()
        writer.release()

        return file_path

    def stop_recording(self) -> None:
        self.is_recording = False

    def overlap_video(self, path: str, time: int, chunk_time: int = 20) -> None:
        """Cut root video into overlapping sub videos. Used for self.start_recording_v1 """
        cap = cv2.VideoCapture(path)
        if not self.cap.isOpened():
            return

        frame_count = 0
        frame_start = 0
        frame_end = time * self.fps
        step = (self.video_duration - self.overlap_time) * self.fps
        self.start_time = datetime.now()

        while frame_end <= chunk_time * self.fps:
            writer = self._start_video_writer(self.start_time + timedelta(seconds=1))
            print("Running.....")
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_start)

            while frame_count < frame_end:
                ret, frame = cap.read()
                if not ret:
                    print("Error: Failed to read.")
                    break

                writer.write(frame)
                frame_count += 1

            frame_start += step
            frame_end += step
            frame_count = frame_start
            self.start_time = self.start_time + timedelta(seconds=step / self.fps)
            writer.release()

    def create_file_path(self, start_time: datetime) -> str:
        """Create file path for video."""
        end_time = start_time + timedelta(seconds=self.video_duration)
        start_timestamp = start_time.strftime("%S-%M-%H-%d-%m-%y")
        end_timestamp = end_time.strftime("%S-%M-%H-%d-%m-%y")

        return os.path.join(self.output_path, f"{start_timestamp}__{end_timestamp}_.mp4")

    def _start_video_writer(self, start_time: datetime, file_path: str = '') -> cv2.VideoWriter:
        """ Create cv2.VideoWriter instance for writing video."""
        file_path = self.create_file_path(start_time) if file_path == '' else file_path
        return cv2.VideoWriter(file_path, self.fourcc, self.fps, (self.frame_width, self.frame_height))

    def cleanup(self) -> None:
        print("Releasing resources...")
        self.cap.release()
        cv2.destroyAllWindows()

    def __del__(self) -> None:
        if self.cap.isOpened():
            self.cleanup()


if __name__ == "__main__":
    # Create a folder saving collected data
    output_folder = "output_folder"
    os.makedirs(output_folder, exist_ok=True)

    recorder = VideoRecorder(video_path='/Users/huynhvietdung/Downloads/1 MINUTE COUNTDOWN TIMER (60 SECONDS TIMER).mp4'
                             , output_path=output_folder)
    # recorder = VideoRecorder(output_path=output_folder)

    recorder.start_recording_v3_2()
