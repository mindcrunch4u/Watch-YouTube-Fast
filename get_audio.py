import requests
import uuid
import urllib
import subprocess
from subprocess import Popen, PIPE, STDOUT
from pathlib import Path
from downloader_probe import probe_id, download_and_save
from configuration import default_config
from arguments_parsing import user_args

def get_audio_to_path(link_to_video):
    if user_args.get_audio_from == "remote":
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
    else:
        #use yt-dlp locally
        print("Starting local audio fetch...")
        audio_format = "mp3"
        output_format="%(title)s-%(id)s.%(ext)s"
        outfile = subprocess.getoutput("yt-dlp --print filename -o \'{}\' {}".format(output_format, link_to_video))
        outfile = Path(outfile).stem + "." + audio_format

        arguments = ["yt-dlp", "-o", output_format, "--extract-audio", "--audio-format", audio_format, link_to_video]
        process = Popen(arguments , stdout=PIPE, stderr=STDOUT, shell=False)
        if default_config.verbose:
            with process.stdout:
                for line in iter(process.stdout.readline, b''): # b'\n'-separated lines
                    try:
                        decoded_line = line.decode()
                    except:
                        decoded_line = str(line)
                    print(decoded_line.strip(), flush=True)
        exitcode = process.wait()
        if exitcode == 0:
            print("Audio saved, status: {} ==> {}".format(exitcode, outfile))
        else:
            print("Local audio fetch failed.")
            print("bort.")
            outfile = None
        return outfile

if __name__ == "__main__":
    get_audio_to_path("https://www.youtube.com/watch?v=5BVfWQq8fAs")
