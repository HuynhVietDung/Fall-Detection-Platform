import cv2
import time
import os
from datetime import datetime, timedelta
import tensorflow as tf
from tensorflow import keras
from requests import Session, Request
import string
import random

start_run_time = datetime.now()

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


output_path = "result_folder_1"
filename = "/Users/huynhvietdung/Downloads/20240328_085650000_iOS.MOV"
hash_id = upload_video(filename)

print("Total time: ", (datetime.now() - start_run_time).seconds)

print(hash_id)
video_url = os.path.join(public_link, hash_id)
video_url = os.path.join(video_url, filename)
print(video_url)

filename = os.path.relpath(filename, output_path)
filename = filename.replace(".MOV", "")
print(filename)

f = open(os.path.join(output_path, f"{filename}.txt"), "w")
f.write(f"{video_url} - {-1} - {-1}\n")
f.close()
