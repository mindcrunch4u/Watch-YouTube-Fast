class DefaultConfig:
    def __init__(self):
        self.proxy_url = ""

default_config = DefaultConfig()

default_config.proxy_url = "http://10.10.0.21:59001"
default_config.site_url = "<your website>"
default_config.downloader_endpoint = "<web-box downloader API>"
default_config.storage_endpoint = "<nginx autoindex URL>"

default_config.verbose = False
default_config.no_audio = True # generate TTS for the summary or not
default_config.support_large_text = True
default_config.split_audio_by_time = 60*15 # <=0 disable splitting, >0 split by seconds, 60*15 split every 15 minutes
default_config.transcription_format = "text" # text, srt, ... use `json` if your API reseller uses a poorly-implemented API proxy server
default_config.large_file_chunk_size = 3000
default_config.base_url="https://hk.xty.app/v1"
default_config.default_model = "gpt-3.5-turbo-0125"
default_config.default_model = "gpt-3.5-turbo-instruct"

import os
proxy = default_config.proxy_url
os.environ['http_proxy'] = proxy
os.environ['HTTP_PROXY'] = proxy
os.environ['https_proxy'] = proxy
os.environ['HTTPS_PROXY'] = proxy

if not default_config.storage_endpoint.strip().endswith("/"):
    # nginx audioindex ends with a slash, like a folder
    default_config.storage_endpoint = default_config.storage_endpoint.strip() + "/"
if default_config.downloader_endpoint.strip().endswith("/"):
    # Web-Box url does not end with a slash
    default_config.downloader_endpoint = default_config.downloader_endpoint.strip().rstrip("/")
