# https://stackoverflow.com/questions/76813435/how-to-remember-messages-from-different-chatcompletion-instances
from private import openai_key
from openai import OpenAI
from pathlib import Path
import warnings
import httpx
import sys
import os
from subprocess import Popen, PIPE, STDOUT
from get_audio import get_audio_to_path
from configuration import default_config
from arguments_parsing import user_args
from downloader_probe import Spinner

if default_config.support_large_text:
    from largetext import large_text_to_list, default_chunk_size

warnings.filterwarnings("ignore", category=DeprecationWarning)
# filter out OpenAI warning: "DeprecationWarning: Due to a bug, this method doesn't actually stream the response content, `.with_streaming_response.method()` should be used instead"


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
        base_url=default_config.base_url,
        api_key=openai_key,
        http_client=httpx.Client(
            base_url=default_config.base_url,
            follow_redirects=True,
        ),
    )
    return client


client = create_client(openai_key)

def get_tts(text, audio_output_path):

    if default_config.no_audio:
        print("Skip generating TTS.")
        return

    speech_file_path = Path(audio_output_path)

    response = client.audio.speech.create(
      model="tts-1",
      voice="nova",
      input=text
    )

    response.stream_to_file(speech_file_path)
    print("[*] TTS saved to: {}".format(audio_output_path))


def get_completion_streamed(system_prompt, user_prompt):
    ret_string = ""
    completion = client.chat.completions.create(
      model=default_config.default_model,
      messages=[
        {"role": "system", "content": system_prompt },
        {"role": "user", "content": user_prompt}
      ],
      stream=True
    )
    try:
        for response in completion:
            ret_string += response.choices[0].text
    except Exception as e:
        print(e)
        print(response)
        sys.exit(1)
    return ret_string


def get_completion(template_file, transcription_file):

    temp = open(template_file, "r")
    template_content = temp.read()
    temp.close()

    temp = open(transcription_file, "r")
    transcription_content = temp.read()
    temp.close()

    completion_text = None

    default_system_prompt = "You are a helpful assistant. You are good at summarizing transcriptions text from videos. You will help the user to summarize video transcription text."
    chunk_index = 0

    spinner = Spinner()
    spinner.enter()

    if default_config.support_large_text:
        list_of_texts = large_text_to_list(transcription_content)
        list_of_completions = []
        for text_chunk in list_of_texts:
            print("[*] handling chunk: {}".format(chunk_index))
            chunk_index += 1
            completion_text = get_completion_streamed(default_system_prompt, "{}".format(template_content + text_chunk))
            list_of_completions.append(completion_text)

        summary_system_prompt = "The user has multiple chunks of summaries belonging to the same video, there might be overlaps, please combine the summaries into one, handle the overlapping parts appropriately."
        summary_user_prompt = "{}".format(template_content + os.linesep.join(list_of_completions)) 
        completion_text = get_completion_streamed(summary_system_prompt, summary_user_prompt)
    else:
        completion_text = get_completion_streamed(default_system_prompt, "{}".format(template_content + transcription_content))

    spinner.exit()

    temp_filename = os.path.basename(transcription_file)
    completion_file_name = "./completion_{}_file.txt".format(temp_filename)
    with open(completion_file_name, "w") as buffer:
        buffer.write(completion_text)
        buffer.write(os.linesep)
        buffer.close()

    print("[*] Completion saved to: {}".format(completion_file_name))
    return completion_file_name


def get_transcription(audio_file_path):
    transcription_suffix = ""
    if default_config.transcription_format == "text":
        transcription_suffix = "txt"
    else:
        transcription_suffix = default_config.transcription_format

    output_transcription_file_name = Path(audio_file_path).stem + ".{}".format(transcription_suffix)

    if user_args.get_transcription_from == "local":
        arguments = ["whisper", audio_file_path, "--output_format", transcription_suffix, "--output_dir", "./"]
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

        spinner = Spinner()
        spinner.enter()
        audio_file= open(audio_file_path, "rb")
        transcription = client.audio.transcriptions.create(
          file=audio_file,
          model="whisper-1",
          response_format=default_config.transcription_format
        )
        spinner.exit()
        with open(output_transcription_file_name, "w") as f:
            response_text = transcription.text
            if default_config.verbose:
                print(response_text)
            f.write(response_text)
    print("[*] Transcription saved to: {}.".format(transcription_file))
    return output_transcription_file_name


if __name__ == "__main__":

    if (user_args.is_full_procedure or
        (user_args.start_from_stage == 1 and not user_args.is_single_command)):
        print("[*] Starting downloader ...")
        audio_path = get_audio_to_path(user_args.content)
        print("[*] Audio saved to: {}, starting transcription...".format(audio_path))

        transcription_file = get_transcription(audio_path)

        completion_file_name = get_completion(user_args.template, transcription_file)
        completion_text = None
        with open(completion_file_name, "r") as comp:
            completion_text = comp.read()
            comp.close()

        print("[*] Waiting for TTS...")
        tts_file_name = "./speech_{}_file.mp3".format(os.path.basename(completion_file_name))
        get_tts(completion_text, tts_file_name)

    elif not user_args.is_single_command:
        if user_args.start_from_stage == 1:
            # covered in the "full-procedure" case
            pass
        elif user_args.start_from_stage == 2:
            audio_path = user_args.content
            print("[*] Using audio file: {}, starting transcription...".format(audio_path))
            transcription_file = get_transcription(audio_path)

            completion_file_name = get_completion(user_args.template, transcription_file)

            completion_text = None
            with open(completion_file_name, "r") as comp:
                completion_text = comp.read()
                comp.close()
            print("[*] Waiting for TTS...")
            tts_file_name = "./speech_{}_file.mp3".format(os.path.basename(completion_file_name))
            get_tts(completion_text, tts_file_name)
        elif user_args.start_from_stage == 3:
            transcription_file = user_args.content
            print("[*] Using transcription: {}, starting completion...".format(transcription_file))
            completion_file_name = get_completion(user_args.template, transcription_file)

            completion_text = None
            with open(completion_file_name, "r") as comp:
                completion_text = comp.read()
                comp.close()
            print("[*] Waiting for TTS...")
            tts_file_name = "./speech_{}_file.mp3".format(os.path.basename(completion_file_name))
            get_tts(completion_text, tts_file_name)
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

    else: # single command mode
        if user_args.start_from_stage == 1:
            # only download audio
            print("[*] Starting downloader ...")
            audio_path = get_audio_to_path(user_args.content)
            print("[*] Audio saved to: {}.".format(audio_path))
        elif user_args.start_from_stage == 2:
            # only generate transcription
            audio_path = user_args.content
            transcription_file = get_transcription(audio_path)
        elif user_args.start_from_stage == 3:
            # only generate completion
            transcription_file = user_args.content
            completion_file_name = get_completion(user_args.template, transcription_file)
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
