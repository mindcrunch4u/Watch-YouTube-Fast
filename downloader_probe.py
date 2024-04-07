import sys
import time
import requests
import subprocess
from subprocess import Popen, PIPE, STDOUT
from urllib.parse import unquote
from lxml import etree
from io import StringIO
from configuration import default_config

import unicodedata # slugify
import re # slugify

headers = {
"Host": default_config.site_url,
"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
"Accept-Language": "en-US,en;q=0.5",
"Accept-Encoding": "gzip, deflate, br",
"Connection": "keep-alive",
"Upgrade-Insecure-Requests": "1",
"Sec-Fetch-Dest": "document",
"Sec-Fetch-Mode": "navigate",
"Sec-Fetch-Site": "same-origin",
"Sec-Fetch-User":"?1",
        }

# cd default_storage
# python -m http.server 5000
parser = etree.HTMLParser()
request_object = None

def req_object():
    global request_object
    if request_object == None:
        request_object = requests.Session()
    return request_object


def get_link_from_result(result):
    html = result.content.decode("utf-8")
    tree = etree.parse(StringIO(html), parser=parser)
    refs = tree.xpath("//a")
    links = [link.get('href', '') for link in refs]
    return links[0]


def return_if_found(request_endpoint, is_debug=False):
    probe_delay = 5
    while True:
        try:
            result = req_object().get(request_endpoint, verify=(not is_debug), headers=headers)
            if result.status_code == 200:
                return result
            else:
                print("Probing for path: {}...".format(request_endpoint))
        except Exception as e:
            print(e)
            return None
        time.sleep(probe_delay)


def probe_id(storage_endpoint, post_id, is_debug):
    # probe folder
    print("Looking into folder...")
    post_endpoint = "{}/{}/".format(storage_endpoint, post_id)
    result = return_if_found(post_endpoint, is_debug)

    # probe confirmation
    print("Looking for confirmation...")
    post_endpoint = "{}/{}/{}".format(storage_endpoint, post_id, "confirmation")
    result = return_if_found(post_endpoint, is_debug)
    confirmation_code = int(result.content.decode().strip())

    if confirmation_code == 1:
        print("Looking for download link...")
        post_endpoint = "{}/{}/{}/".format(storage_endpoint, post_id, "datablock")
        res = requests.get(post_endpoint)
        link = get_link_from_result(res)
        link = "{}/{}/{}/{}".format(storage_endpoint, post_id, "datablock", link)
        print("Download link found: {}".format(link))
        return link
    else:
        return None

def create_compatible_name(value, allow_unicode=True):
    """
    https://stackoverflow.com/questions/295135/turn-a-string-into-a-valid-filename
    Taken from https://github.com/django/django/blob/master/django/utils/text.py
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value.lower())
    return re.sub(r'[-\s]+', '-', value).strip('-_')


def download_and_save(from_link, to_folder="./"):
    unquoted_from_link = create_compatible_name(unquote(from_link).split("/")[-1]) # prevents linux-incompatible names
    unquoted_from_link += ".mp3"
    process = Popen(["/usr/bin/curl", "-s", from_link, "-o", unquoted_from_link ])
    exitcode = process.wait()
    if exitcode != 0:
        return -1

    process = Popen(["/usr/bin/mkdir", "-p", to_folder])
    exitcode = process.wait()
    if exitcode != 0:
        return -2

    file_name = from_link.split("/")[-1]
    target_file_name = "{}/{}".format(to_folder, unquoted_from_link)
    process = Popen(["/usr/bin/mv", file_name, target_file_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    exitcode = process.wait()

    return target_file_name


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 script.py <ID>")
        sys.exit(1)

    is_debug = True
    storage_endpoint="http://127.0.0.1:5000"
    link = probe_id(storage_endpoint, sys.argv[1], is_debug)
    outfile = download_and_save(link)
    print(outfile)
