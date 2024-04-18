import threading
from subprocess import Popen, PIPE, STDOUT

links_file = "./video_links.txt"
template = "./template_cn.txt"

"""
echo "..." > temp.txt
cat completion_* > all_comp.txt
python understand.py -o -s 3 -t temp.txt -c all_comp.txt
"""

def run_command(arguments, is_shell=True):

    print("Command: {}".format(" ".join(arguments)))
    if is_shell:
        arguments = " ".join(arguments)
    process = Popen(arguments , stdout=PIPE, stderr=STDOUT, shell=is_shell)
    thread_id = threading.current_thread().name

    with process.stdout:
        for line in iter(process.stdout.readline, b''): # b'\n'-separated lines
            try:
                decoded_line = line.decode()
            except:
                decoded_line = str(line)
            print("[{}] {}".format(thread_id, decoded_line), flush=True)
    exitcode = process.wait()
    return exitcode

def get_completion_for_link(video_link):
    args = ["python", "understand.py", "-t", template, "-c", video_link]
    run_command(args)

def main():
    links = []
    with open(links_file, "r") as f:
        links = f.readlines()
        f.close()
    links = [l.strip() for l in links]

    threads = []
    for item in links:
        t = threading.Thread(target=get_completion_for_link, args=[item,])
        t.start()
        threads.append(t)

    for t in threads:
        t.join()
    print("Batch Processing Complete.")

if __name__ == "__main__":
    main()
