

## Usage

### Configuration

Configure the following fields in `configuration.py`:
-`site_url`, this is for request headers. The script assumes the `downloader_endpoint` and `storage_endpoint` are using the same FQDN.
-`downloader_endpoint`, set up a remote downloader using the [Web-Box](https://github.com/mindcrunch4u/Web-Box) project. Copy the server's endpoint here.
-`storage_endpoint`, set up an `autoindex`-like, HTTP-based file server. Copy the server's root endpoint here.

### Trying it out

**Turn a YouTube link into a TTS summary**
```
python understand.py \ 
    --full-procedure <link> \
    --stage1-get-audio <remote|local> \
    --stage2-get-transcription <remote|local> \
    --stage3-get-completion <remote|local> \
    --stage4-get-tts <remote|local>
```

***Single Steps**: perform each step manually*
```
python understand.py --stage1-get-audio <remote|local> <link>
python understand.py --stage2-get-transcription <remote|local> <path/to/audio/file>
python understand.py --stage3-get-completion <remote|local> <path/to/transcription/file>
python understand.py --stage4-get-tts <remote|local> <path/to/completion/text>
```

***Start From Stage 2**: assume you already have the audio file, and you want to complete the rest of the process:*
```
python understand.py --start-from-stage2 \
    --stage2-get-transcription <remote|local> <path/to/audio/file>
    --stage3-get-completion <remote|local>\
    --stage4-get-tts <remote|local>
```

***Start From Stage 3**: assume you already have the transcription file, and you want to complete the rest of the process:*
```
python understand.py --start-from-stage3
    --stage3-get-completion <remote|local> <path/to/transcription/file>
    --stage3-get-completion <remote|local>\
    --stage4-get-tts <remote|local>
```
