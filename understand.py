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
from arguments_parsing import user_args

"""
Description:
    4 main functions:
    - get_audio_to_path():
        input: a YouTube link
        output: path to the downloaded audio file.
    - get_transcription():
        input: path to a mp3 file
        output: is the path to the transcription file.
    - get_completion():
        two inputs: 1) path to the template file, 2) path to the transcription file.
        output: path to the completion text file.
    - get_tts():
        two inputs: 1) a string containing text, 2) TTS output file name, should end in .mp3.
        output: path to the TTS audio file.
"""

def usage():
    print("python3 understand.py <template.txt> <transcription.txt | video link>")

def create_client(openai_key):
    client = OpenAI(
        base_url="https://hk.xty.app/v1",
        api_key=openai_key,
        http_client=httpx.Client(
            base_url="https://hk.xty.app/v1",
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

    temp_filename = os.path.basename(transcription_file)
    completion_file_name = "./completion_{}_file.txt".format(temp_filename)
    completion_text = completion.choices[0].message.content
    with open(completion_file_name, "w") as buffer:
        buffer.write(completion_text)
        buffer.close()

    return completion_file_name


def get_transcription(audio_file_path):
    output_transcription_file_name = Path(audio_file_path).stem + ".txt"
    if user_args.get_transcription_from == "local":
        arguments = ["whisper", audio_file_path, "--output_format", "txt", "--output_dir", "./"]
        print("[*] {}".format(" ".join(arguments)))
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
        print("[*] Transcription exit status: {}".format(exitcode))
    else:
        # get transcription from remote
        file_stats = os.stat(audio_file_path)
        audio_file_size_in_mb = file_stats.st_size / (1024 * 1024)
        if audio_file_size_in_mb > 20:
            print("[!] Sending a audio file larger than 20MB might fail. Use local transcription instead.")
            print("[!] Abort.")
            sys.exit(1)
        print("[*] Getting transcription from remote...")
        # use remote transcription
        client = create_client(openai_key)

        audio_file= open(audio_file_path, "rb")
        transcription = client.audio.transcriptions.create(
          model="whisper-1",
          file=audio_file
        )
        if default_config.verbose:
            print(transcription.text)
        with open(output_transcription_file_name, "w") as f:
            f.write(transcription.text)
            f.close()
    return output_transcription_file_name

if __name__ == "__main__":

    if (user_args.is_full_procedure or
        (user_args.start_from_stage == 1 and not user_args.is_single_command)):
        audio_path = get_audio_to_path(user_args.content)
        print("[*] Audio saved to: {}, starting transcription...".format(audio_path))

        transcription_file = get_transcription(audio_path)
        print("[*] Transcription saved to: {}, starting completion...".format(transcription_file))

        completion_file_name = get_completion(user_args.template, transcription_file)
        completion_text = None
        print("[*] Completion saved to: {}".format(completion_file_name))
        with open(completion_file_name, "r") as comp:
            completion_text = comp.read()
            comp.close()

        print("[*] Waiting for TTS...")
        tts_file_name = "./speech_{}_file.mp3".format(os.path.basename(completion_file_name))
        get_tts(completion_text, tts_file_name)
        print("[*] TTS saved to: {}".format(tts_file_name))

    elif not user_args.is_single_command:
        if user_args.start_from_stage == 1:
            # covered in the "full-procedure" case
            pass
        elif user_args.start_from_stage == 2:
            audio_path = user_args.content
            print("[*] Using audio file: {}, starting transcription...".format(audio_path))
            transcription_file = get_transcription(audio_path)
            print("[*] Transcription saved to: {}.".format(transcription_file))

            completion_file_name = get_completion(user_args.template, transcription_file)
            print("[*] Completion saved to: {}".format(completion_file_name))

            completion_text = None
            with open(completion_file_name, "r") as comp:
                completion_text = comp.read()
                comp.close()
            print("[*] Waiting for TTS...")
            tts_file_name = "./speech_{}_file.mp3".format(os.path.basename(completion_file_name))
            get_tts(completion_text, tts_file_name)
            print("[*] TTS saved to: {}".format(tts_file_name))
        elif user_args.start_from_stage == 3:
            transcription_file = user_args.content
            print("[*] Using transcription: {}, starting completion...".format(transcription_file))
            completion_file_name = get_completion(user_args.template, transcription_file)
            print("[*] Completion saved to: {}".format(completion_file_name))

            completion_text = None
            with open(completion_file_name, "r") as comp:
                completion_text = comp.read()
                comp.close()
            print("[*] Waiting for TTS...")
            tts_file_name = "./speech_{}_file.mp3".format(os.path.basename(completion_file_name))
            get_tts(completion_text, tts_file_name)
            print("[*] TTS saved to: {}".format(tts_file_name))
        elif user_args.start_from_stage == 4:
            completion_file_name = user_args.content
            print("[*] Using completion: {}, starting TTS...".format(completion_file_name))
            completion_text = None
            with open(completion_file_name, "r") as comp:
                completion_text = comp.read()
                comp.close()
            print("[*] Waiting for TTS...")
            tts_file_name = "./speech_{}_file.mp3".format(os.path.basename(completion_file_name))
            get_tts(completion_text, tts_file_name)
            print("[*] TTS saved to: {}".format(tts_file_name))

    else: # single command mode
        if user_args.start_from_stage == 1:
            # only download audio
            audio_path = get_audio_to_path(user_args.content)
            print("[*] Audio saved to: {}.".format(audio_path))
        elif user_args.start_from_stage == 2:
            # only generate transcription
            audio_path = user_args.content
            transcription_file = get_transcription(audio_path)
            print("[*] Transcription saved to: {}.".format(transcription_file))
        elif user_args.start_from_stage == 3:
            # only generate completion
            transcription_file = user_args.content
            completion_file_name = get_completion(user_args.template, transcription_file)
            print("[*] Completion saved to: {}".format(completion_file_name))
        elif user_args.start_from_stage == 4:
            # only generate TTS
            completion_file_name = user_args.content
            completion_text = None
            with open(completion_file_name, "r") as comp:
                completion_text = comp.read()
                comp.close()
            print("[*] Waiting for TTS...")
            tts_file_name = "./speech_{}_file.mp3".format(os.path.basename(completion_file_name))
            get_tts(completion_text, tts_file_name)
            print("[*] TTS saved to: {}".format(tts_file_name))
