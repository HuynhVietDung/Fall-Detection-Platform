from requests import Session, Request
import os
import requests


class IPFSTransfer:
    def __init__(self, public_link: str, api_key: str, secret_key: str) -> None:
        self.public_link = public_link
        self.api_key = api_key
        self.secret_key = secret_key
        self.url = None

    def get_url(self, cid: str, file_path: str) -> str:
        """Return retrieval URL to file on IPFS."""
        return f"https://{self.public_link}/ipfs/{cid}/{file_path}"

    def upload_video(self, file_path: str) -> str:
        """
        Uploads a video file to the IPFS network using the Pinata API.
        It uses the provided API and secret keys for authentication and returns the
        IPFS hash of the uploaded file upon successful upload.
        """

        ipfs_url = "https://api.pinata.cloud/pinning/pinFileToIPFS"
        headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.146 Safari/537.36",
            "pinata_api_key": self.api_key, 
            "pinata_secret_api_key": self.secret_key,
        }
        
        with open(file_path, "rb") as file:
            files = [("file", (os.path.basename(file_path), file))]
            request = Request("POST", ipfs_url, headers=headers, files=files).prepare()
            response = Session().send(request)
        
        if response.json().get("IpfsHash") == None:
            raise Exception("Cannot upload video to Pinata Gateway.")

        return response.json().get("IpfsHash")


    def download_video(self, dest_folder: str, cid: str, file_path: str) -> None:
        """
        Download a file from IPFS via Pinata Gateway and save it locally. 
        """

        # Define file url
        self.url = self.set_url(file_path)

        if not os.path.exists(dest_folder):
            os.makedirs(dest_folder)  # create folder if it does not exist

        file_name = self.url.split('/')[-1].replace(" ", "_") 
        path = os.path.join(dest_folder, file_name)

        r = requests.get(self.url, stream=True)
        if r.ok: # HTTP status code 200
            print("Saving to", os.path.abspath(path))
            with open(path, 'wb') as f:  # write file
                for chunk in r.iter_content(chunk_size=1024 * 8):
                    if chunk:
                        f.write(chunk)
                        f.flush()
                        os.fsync(f.fileno())
        else:  # HTTP status code 4XX/5XX
            print("Download failed: status code {}\n{}".format(r.status_code, r.text))

