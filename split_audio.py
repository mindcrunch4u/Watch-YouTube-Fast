import os
from configuration import default_config
from subprocess import Popen, PIPE, STDOUT

def split_audio_by_seconds(audio_file_path, seconds):
    # return a list of splitted files
    audio_file_path = os.path.normpath(audio_file_path)
    base_file_name = os.path.basename(audio_file_path)
    arguments = ["ffmpeg", "-y", "-i", "\'{}\'".format(audio_file_path), "-f", "segment", "-segment_time", seconds, "-c", "copy", "\'split_audio_{}_%05d.mp3\'".format(base_file_name)]
    temp_string_arguments = [str(a) for a in arguments]
    print("[*] {}".format(" ".join(temp_string_arguments)))
    process = Popen(" ".join(temp_string_arguments) , stdout=PIPE, stderr=STDOUT, shell=True)
    split_names = []
    with process.stdout:
        for line in iter(process.stdout.readline, b''): # b'\n'-separated lines
            decoded_line = ""
            try:
                decoded_line = line.decode()
            except:
                decoded_line = str(line)
            if default_config.verbose:
                print("{}".format(decoded_line), flush=True)
            if "Opening" in decoded_line and "for writing" in decoded_line:
                split_name = decoded_line.split("Opening")[1].split("for writing")[0].strip().strip("\'").strip()
                split_names.append(split_name)
                if True:
                    print("Generated Split: {}".format(split_name))
    exitcode = process.wait()
    return split_names

if __name__ == "__main__":
    split_audio_by_seconds("long_audio.mp4.mp3", 600)
