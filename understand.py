# https://stackoverflow.com/questions/76813435/how-to-remember-messages-from-different-chatcompletion-instances
from private import openai_key
from openai import OpenAI
from pathlib import Path
import httpx
import sys
import os
from subprocess import Popen, PIPE, STDOUT
from get_audio import get_audio_to_path
from configuration import default_config

proxy = default_config.proxy_url

os.environ['http_proxy'] = proxy
os.environ['HTTP_PROXY'] = proxy
os.environ['https_proxy'] = proxy
os.environ['HTTPS_PROXY'] = proxy

is_download_audio_remotely=default_config.is_download_audio_remotely
is_generate_tts_only = default_config.is_generate_tts_only

def usage():
    print("python3 understand.py <template.txt> <transcription.txt | video link>")

def create_client(openai_key):
    client = OpenAI(
        base_url="https://api.xty.app/v1",
        api_key=openai_key,
        http_client=httpx.Client(
            base_url="https://api.xty.app/v1",
            follow_redirects=True,
        ),
    )
    return client

def get_tts(text, audio_output_path):

    speech_file_path = Path(audio_output_path)
    client = create_client(openai_key)

    response = client.audio.speech.create(
      model="tts-1",
      voice="nova",
      input=text
    )

    response.stream_to_file(speech_file_path)

def get_completion(template_file, transcription_file):

    temp = open(template_file, "r")
    template_content = temp.read()
    temp.close()

    temp = open(transcription_file, "r")
    transcription_content = temp.read()
    temp.close()

    client = create_client(openai_key)

    completion = client.chat.completions.create(
      model="gpt-3.5-turbo-0125",
      messages=[
        {"role": "system", "content": "You are a helpful assistant. You are good at summarizing transcriptions text from videos. You will help the user to summarize video transcription text."},
        {"role": "user", "content": "{}".format(template_content + transcription_content)}
      ]
    )

    return completion.choices[0].message.content


def get_transcription(audio_file_path):
    output_transcription_file_name = Path(audio_file_path).stem + ".txt"
    if default_config.is_use_local_transcription:
        arguments = ["whisper", audio_file_path, "--output_format", "txt", "--output_dir", "./"]
        print("[*] {}".format(" ".join(arguments)))
        process = Popen(arguments , stdout=PIPE, stderr=STDOUT, shell=False)
        with process.stdout:
            for line in iter(process.stdout.readline, b''): # b'\n'-separated lines
                try:
                    decoded_line = line.decode()
                except:
                    decoded_line = str(line)
                print(decoded_line.strip(), flush=True)
        exitcode = process.wait()
        print("[*] Transcription exit status: {}".format(exitcode))
    else:
        print("[*] Getting transcription from remote...")
        # use remote transcription
        client = create_client(openai_key)

        audio_file= open(audio_file_path, "rb")
        transcription = client.audio.transcriptions.create(
          model="whisper-1",
          file=audio_file
        )
        #print(transcription.text)
        with open(output_transcription_file_name, "w") as f:
            f.write(transcription.text)
            f.close()
    return output_transcription_file_name

if __name__ == "__main__":
    if len(sys.argv) != 3:
        usage()
        sys.exit(1)

    template_file = str(sys.argv[1])
    transcription = None

    if is_download_audio_remotely and not is_generate_tts_only:
        audio_path = get_audio_to_path(sys.argv[2])
        print("[*] Audio saved to: {}, starting transcription...".format(audio_path))
        transcription_file = get_transcription(audio_path)
    else:
        transcription_file = str(sys.argv[2])

    completion_file_name = None
    completion_text = None
    if not is_generate_tts_only:
        temp_filename = os.path.basename(transcription_file)
        print("[*] Waiting for Completion...")
        completion_text = get_completion(template_file, transcription_file)
        completion_file_name = "./completion_{}_file.txt".format(temp_filename)
        with open(completion_file_name, "w") as buffer:
            buffer.write(completion_text)
            buffer.close()
            print("[*] Completion saved to: {}".format(completion_file_name))
    else:
        completion_file_name = sys.argv[2]
        with open(completion_file_name, "r") as completion_file:
            completion_text = completion_file.read()

    print("[*] Waiting for TTS...")
    tts_file_name = "./speech_{}_file.mp3".format(os.path.basename(completion_file_name))
    get_tts(completion_text, tts_file_name)
    print("[*] TTS saved to: {}".format(tts_file_name))

