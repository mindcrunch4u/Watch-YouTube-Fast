import argparse
import validators
import sys
import os
from tabulate import tabulate

def get_arguments():

    parser = argparse.ArgumentParser(
                        prog='Understand',
                        description='Turn a YouTube link into a TTS summary. Listen to a customizable summary, which saves your time and does not strain your eyes.',
                        epilog="The \"remote\" and \"local\" in the arguments refer to services used."
                        )

    parser.add_argument("-f", "--full-procedure", action= "store_true",
                        help="Goes through the entire procedure of downloading-transcribing-completing and TTS generating. Requires all of the following arguments to be set.")
    parser.add_argument("-s", "--start-from-stage", choices=[1, 2, 3, 4], default=1, type=int,
                        help="Instructs the script to start from a certain stage, skipping previous stages.")
    parser.add_argument("-o", "--is-single", action = "store_true",
                        help="If single command is used, only the stage itself will be executed.")

    parser.add_argument("-c", "--content", type=str,
                        help="Specify a link or an audio file, or a text file. This depends on other options.")
    parser.add_argument("-t", "--template", type=str,
                        default="./template.txt",
                        help="Specify a template file, its content will be prepended to the completion prompt.")
    parser.add_argument("-s1", "--stage1-get-audio", type=str, choices=["remote", "local"],
                        default="remote",
                        help="Specify audio retrieval method. Remote uses Web-Box, while local uses yt-dlp locally.")
    parser.add_argument("-s2", "--stage2-get-transcription", type=str, choices=["remote", "local"],
                        default="remote",
                        help="Specify transcription retrieval method. Remote uses OpenAI whisper, while local uses the whisper tool locally.")
    parser.add_argument("-s3", "--stage3-get-completion", type=str, choices=["remote", "local"],
                        default="remote",
                        help="Specify completion retrieval method. Remote uses OpenAI's ChatGPT, local uses a locally installed model.")
    parser.add_argument("-s4", "--stage4-get-tts", type=str, choices=["remote", "local"],
                        default="remote",
                        help="Specify TTS retrieval method. Remote uses OpenAI's Speech-to-Text, local uses a locally installed TTS model.")

    args = parser.parse_args()

    get_audio_from="remote"

    is_full_procedure = args.full_procedure
    start_from_stage = args.start_from_stage
    is_single_command = args.is_single
    template = args.template
    get_audio_from = args.stage1_get_audio
    get_transcription_from = args.stage2_get_transcription
    get_completion_from = args.stage3_get_completion
    get_tts_from = args.stage4_get_tts
    content = args.content

    print()
    print(tabulate(
                [[is_full_procedure, start_from_stage, is_single_command, template, content, get_audio_from, get_transcription_from, get_completion_from, get_tts_from]],
                headers=["full procedure", "from stage", "single command", "template", "content", "audio(s1)", "transcription(s2)", "completion(s3)", "TTS(s4)"], tablefmt='orgtbl'
                ))
    print()

    # Validate script launch mode
    
    if is_full_procedure and (start_from_stage != 1):
        print("[-] To use the full-procedure, the script must start from stage 1.")
        sys.exit(1)

    if is_full_procedure and is_single_command:
        print("[-] The full-procedure and \"single command\" cannot coexist.")
        sys.exit(1)

    # Validate full-procedure mode arguments

    if is_full_procedure:
        if template == None or content == None:
            print("[-] Template (-t) and Content (-c) must be specified when using full-procedure.")
            sys.exit(1)
        if get_audio_from == "remote" and (not validators.url(content)):
            print("[-] Content (-c) must be a URL (such as a YouTube link) when using full-procedure.")
            sys.exit(1)
        if not os.path.isfile(template):
            print("[-] Template (-t) file does not exit.")
            sys.exit(1)

    # Validate non-full mode arguments

    else:
        if start_from_stage == 1:
            if get_audio_from == "remote" and (not validators.url(content)):
                print("[-] Content (-c) must be a URL (such as a YouTube link) when fetching audio.")
                sys.exit(1)
                #TODO: check if yt-dlp is installed
        if start_from_stage == 2:
            if (not content or
                not os.path.isfile(content)):
                print("[-] Content (-c) must be an mp3 audio file when generating transcription.")
                print("[-] file does not exist: {}".format(content))
                sys.exit(1)
                #TODO: check if whisper is installed
            if not str(content).endswith(".mp3"):
                print("[-] Content (-c) must be an mp3 audio file when generating transcription.")
        if start_from_stage == 3:
            if (not content or
                not os.path.isfile(content)):
                print("[-] Content (-c) must be a transcription text file when getting completion (summary).")
                print("[-] file does not exist: {}".format(content))
                sys.exit(1)
                #TODO: check if a local model is installed
        if start_from_stage == 4:
            if (not content or
                not os.path.isfile(content)):
                print("[-] Content (-c) must be a summary text file when getting TTS.")
                print("[-] file does not exist: {}".format(content))
                sys.exit(1)
                #TODO: check if local TTS model is available

if __name__ == "__main__":
    get_arguments()
