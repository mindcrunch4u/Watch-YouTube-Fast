class DefaultConfig:
    def __init__(self):
        self.proxy_url = "http://10.10.0.21:59001"

default_config = DefaultConfig()
default_config.is_download_audio_remotely=True
default_config.is_generate_tts_only = False
default_config.site_url = "<your website>"
default_config.downloader_endpoint = "<web-box downloader API>"
default_config.storage_endpoint = "<nginx autoindex URL>"
