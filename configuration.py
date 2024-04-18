class DefaultConfig:
    def __init__(self):
        self.proxy_url = ""

default_config = DefaultConfig()

default_config.proxy_url = "http://10.10.0.21:59001"
default_config.site_url = "<your website>"
default_config.downloader_endpoint = "<web-box downloader API>"
default_config.storage_endpoint = "<nginx autoindex URL>"

default_config.verbose = True
default_config.no_audio = True
default_config.support_large_text = False
default_config.large_file_chunk_size = 2000

import os
proxy = default_config.proxy_url
os.environ['http_proxy'] = proxy
os.environ['HTTP_PROXY'] = proxy
os.environ['https_proxy'] = proxy
os.environ['HTTPS_PROXY'] = proxy
