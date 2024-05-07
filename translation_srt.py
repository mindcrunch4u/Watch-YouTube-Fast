from private import openai_key
from openai import OpenAI
import httpx

audio_path="./audio.mp3"

def create_client(openai_key):
    client = OpenAI(
        base_url="https://hk.xty.app/",
        api_key=openai_key,
        http_client=httpx.Client(
            base_url="https://hk.xty.app/",
            follow_redirects=True,
        ),
    )
    return client

def get_translation(audio_file_path):
    # get transcription from remote
    client = create_client(openai_key)

    audio_file= open(audio_file_path, "rb")
    translations = client.audio.translations.create(
      model="whisper-1",
      file=audio_file,
      response_format="srt"
    )
    return translations

if __name__ == "__main__":
    text = get_translation(audio_path)
    print(text)
