import os
import secrets
import time
import logging
import requests
from PIL import Image
from io import BytesIO
from google.cloud import storage


logging.basicConfig(level=logging.DEBUG, format='[%(asctime)s] - [%(levelname)s] - %(message)s')

class BucketStorage:
    """
    Interface for storing data
    """
    def __init__(self):
        self.local_root = "./static/images/generated"
        certificate_path = os.environ.get('THE_BOOK_GOOGLE_APPLICATION_CREDENTIALS')
        if certificate_path != None:
            certificate_path = os.environ.get('THE_BOOK_GOOGLE_APPLICATION_CREDENTIALS')
            self.__storage_client = storage.Client.from_service_account_json(certificate_path)
        else:
            self.__storage_client = storage.Client()
            
        bucket_name = os.environ.get("THE_BOOK_GOOGLE_BUCKET_NAME")
        if bucket_name is None:
            raise Exception("THE_BOOK_GOOGLE_BUCKET_NAME environment variable not set")

        self.__bucket = self.__storage_client.get_bucket(bucket_name)

    def host_image(self, image):
        """
        Hosts a PIL image on Firebase and retrieve its URL.

        :param image: the PIL image to host
        :return: the public URL for the image
        """
        # save the PIL image locally
        file_name = self.generate_unique_filename("png")
        relative_path = f"static/images/generated/"
        full_path = self.local_root + relative_path
        if not os.path.exists(full_path):
            os.makedirs(full_path)
        upload_path = full_path + file_name
        image.save(upload_path)

        # now upload the image to firebase
        image_path = upload_path
        blob = self.__bucket.blob(file_name)
        blob.upload_from_filename(image_path)
        # delete the local copy
        os.remove(image_path)

        # return the URL of the image
        blob.make_public()
        return blob.public_url

    
    def fetch_and_host_image(self, url:str)->str:
        """
        Downloads a remote image and host it on our storage solution

        :param url: url to download the image from
        :return: the URL for the image on our storage
        """
        response = requests.get(url)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content))
        # extension = url.split(".")[-1]
        filename = self.generate_unique_filename("png")
        hosted_url = self.host_image(image)
        return hosted_url

    def generate_unique_filename(self, extension):
        """
        Generates a unique filename based on timestamp

        :param extension: extension for the file (e.g. "png")
        :return: the filename
        """
        timestamp = int(time.time())
        random_str = secrets.token_hex(4)
        return f"{timestamp}_{random_str}.{extension}"