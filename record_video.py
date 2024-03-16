import cv2
import time
import os

id = 0


class VideoRecorder:
    '''
        Read and save realtime data from camera.
    '''

    def __init__(self, output_path, camera_idx=0, record_time=20, overlap_time=3):
        self.cap = cv2.VideoCapture(camera_idx)
        self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fourcc = cv2.VideoWriter_fourcc(*'MP4V')
        self.path = output_path
        self.record_time = record_time  # Time for each video
        self.overlap_time = overlap_time  # Overlap time of each two video
        self.is_recording = False
        self.fps = self.set_fps()  # Frames per second
        self.start_time = None  # start recording time

    def set_fps(self):
        # Set fps for camera
        try:
            frame_rate = self.cap.get(cv2.CAP_PROP_FPS)
            # print("Number of frames per second: ", int(frame_rate))
            return int(frame_rate)
        except ValueError:
            self.cap.set(cv2.CAP_PROP_FPS, 20)  # set default FPS values
            return 20

    def start_recording(self):
        if not self.cap.isOpened():  # check for camera is opened
            print("Error: Could not open camera.")
            return

        time.sleep(1)  # wait 1s for start camera

        self.start_time = time.time()
        self.is_recording = True

        file_path = self._record()  # start recording
        self.overlap_video(file_path, 10)

        os.remove(file_path)

    def _record(self):
        global id
        file_name = os.path.join(self.path, f'output_{id}.mp4')
        id += 1
        out = cv2.VideoWriter(file_name, self.fourcc, self.fps, (self.frame_width, self.frame_height))
        print("Running.....")

        frame_count = 0
        frame_end = self.record_time * self.fps

        while self.is_recording and (frame_count <= frame_end):
            ret, frame = self.cap.read()
            if not ret:
                print("Error: Failed to read.")
                return None

            frame = cv2.flip(frame, 1)
            out.write(frame)
            # cv2.imshow("Camera Feed", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):  # Press 'Q' to stop recording
                print(f'Total runtime: {time.time() - self.start_time}')
                break

            frame_count += 1

        self.stop_recording()
        out.release()

        return file_name

    def stop_recording(self):
        self.is_recording = False

    def overlap_video(self, path, time):
        cap = cv2.VideoCapture(path)
        if not self.cap.isOpened():
            return

        frame_count = 0
        frame_start = 0
        frame_end = time * self.fps
        step = self.overlap_time * self.fps

        while frame_end <= self.record_time * self.fps:
            global id
            file_path = os.path.join(self.path, f'output_{id}.mp4')
            id += 1
            out = cv2.VideoWriter(file_path, self.fourcc, self.fps, (self.frame_width, self.frame_height))
            print("Running.....")
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_start)

            while frame_count <= frame_end:
                ret, frame = cap.read()
                if not ret:
                    print("Error: Failed to read.")
                    break

                out.write(frame)
                frame_count += 1

            frame_start += step
            frame_end += step
            frame_count = frame_start
            out.release()

    def cleanup(self):
        print("Releasing resources...")
        self.cap.release()
        cv2.destroyAllWindows()

    def __del__(self):
        if self.cap.isOpened():
            self.cleanup()


if __name__ == "__main__":
    # Create a folder saving collected data
    output_folder = "output_folder"
    os.makedirs(output_folder, exist_ok=True)

    recorder = VideoRecorder(output_path=output_folder)
    recorder.start_recording()
