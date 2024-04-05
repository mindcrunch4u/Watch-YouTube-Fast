import requests
import uuid
import urllib
from downloader_probe import probe_id, download_and_save
from configuration import default_config

import os

proxy = default_config.proxy_url

os.environ['http_proxy'] = proxy
os.environ['HTTP_PROXY'] = proxy
os.environ['https_proxy'] = proxy
os.environ['HTTPS_PROXY'] = proxy

def get_audio_to_path(link_to_video):
    # send request to downloader, use UUID as post ID
    print("Sending download request...")
    created_post_id = str(uuid.uuid4())
    url = default_config.downloader_endpoint
    data = {
            "content" : link_to_video,
            "post_id" : created_post_id,
            "submit" : "Schicken",
            }

    response = requests.post(url, data=data)
    if "Posted." not in response.text:
        print("Err: cannot send download request to server.")
        print(response.text)
        return None
    else:
        print("Request sent, id: {}".format(created_post_id))

    # monitor post ID and download the audio
    storage_endpoint = default_config.storage_endpoint
    link = probe_id(storage_endpoint, created_post_id, False)
    outfile = download_and_save(link)
    print("Saved audio to: {}".format(outfile))

    # return the path to the audio file
    return outfile

if __name__ == "__main__":
    get_audio_to_path("https://www.youtube.com/watch?v=5BVfWQq8fAs")
