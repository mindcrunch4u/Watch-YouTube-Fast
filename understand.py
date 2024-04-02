# https://stackoverflow.com/questions/76813435/how-to-remember-messages-from-different-chatcompletion-instances
from private import openai_key
from openai import OpenAI
from pathlib import Path
import httpx
import sys
import os

def usage():
    print("python3 understand.py <template.txt> <transcription.txt>")

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

def get_audio(text, audio_output_path):

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

if __name__ == "__main__":
    if len(sys.argv) != 3:
        usage()
        sys.exit(1)

    template_file = str(sys.argv[1])
    transcription_file = str(sys.argv[2])

    print("[*] Waiting for Completion...")
    text = get_completion(template_file, transcription_file)

    print("[*] Waiting for Audio...")
    temp_filename = os.path.basename(transcription_file)
    get_audio(text, "./speech_{}_file.mp3".format(temp_filename))
