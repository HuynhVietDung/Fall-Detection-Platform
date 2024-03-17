# TODO: this code is not checked

import cv2
import os


def create_folders(output_folder,  n_videos=0):
    # Create the output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    # Create sub folders
    for i in range(n_videos):
        os.makedirs(f"{output_folder}/{i + 1}",  exist_ok=True)


def capture_frames(input_path, output_path, record_time):
    """
    Extract frames of 'path' in a specified time duration.
    """

    cap = cv2.VideoCapture(input_path)

    # Check if camera is opened successfully
    if not cap.isOpened():
        print("Error opening video capture device.")
        exit(0)

    # Get the frame rate of the video
    try:
        frame_rate = cap.get(cv2.CAP_PROP_FPS)
        fps = int(frame_rate)
        print("Number of frames per second: ", fps)
    except ValueError:
        print("cv2.CAP_PROP_FPS returns 'nan' value. Set the value to the fault 30 fps.")
        cap.set(cv2.CAP_PROP_FPS, 20)  # set default FPS values
        fps = 20

    start_time = 0

    total_frame = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Calculate total frames to extract
    num_frames = fps * record_time

    # Calculate the start frame
    start_frame = fps * start_time

    # Seek to the start frame
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

    # Frame count
    frame_count = 0

    while frame_count < min(num_frames, total_frame):
        # Read a frame
        ret, frame = cap.read()

        if not ret:
            print("Error: Failed to read")
            break

        # Filename with timestamp and frame number
        second = (frame_count // fps) + 1
        frame_number = int((frame_count + start_frame) % fps) + 1

        filename = f"{output_path}/{second}_{frame_number}.jpg"
        frame_count += 1

        # Save frame as image
        cv2.imwrite(filename, frame)

    # Release the capture object
    cap.release()

    # Close all windows
    cv2.destroyAllWindows()
