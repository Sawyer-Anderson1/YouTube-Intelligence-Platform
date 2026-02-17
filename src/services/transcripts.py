# imports:
# os is inprted to access the YouTube API key
# json, time, random, Path imported
# concurrent.futures imported for concurrency
# the youtube transcript api is imported to get the transcripts
# import the proxy config for webshare, to be able to rotate proxies and access the transcripts
import os
import json
import time
import random
import re
from pathlib import Path

import concurrent.futures
from concurrent.futures import ThreadPoolExecutor

# import the function to chunk the transcripts
from chunk_transcripts import read_and_chunk_transcript

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import WebshareProxyConfig
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
    NotTranslatable,
    TranslationLanguageNotAvailable,
    CookiePathInvalid,
    FailedToCreateConsentCookie,
    YouTubeRequestFailed
)

# config 
MAX_WORKERS = 5 # kept low to avoid YouTube rate limiting
MAX_RETRIES = 3 # retry some errors this much
BASE_DELAY = 2.0 # seconds - base for exponential backoff
JITTER_MAX = 2.0 # extra random seconds before each transcript fetch

# get the webshare proxy information
WEBSHARE_PROXY_USER = os.getenv('WEBSHARE_PROXY_USER')
WEBSHARE_PROXY_PASSWORD = os.getenv('WEBSHARE_PROXY_PASSWORD')

if not WEBSHARE_PROXY_USER or not WEBSHARE_PROXY_PASSWORD:
    print("Error: Proxy environment variables are not set.")
    exit(1)

# read in the YouTubeTranscriptApi
ytt_api = YouTubeTranscriptApi(
    proxy_config=WebshareProxyConfig(
        proxy_username=WEBSHARE_PROXY_USER,
        proxy_password=WEBSHARE_PROXY_PASSWORD,
        filter_ip_locations=["us"],
    )
)

# make directory for transcripts
folder_path_pathlib = Path(__file__).parent.parent.parent / 'data' / 'transcripts'
os.makedirs(folder_path_pathlib, exist_ok=True)

# regex to clean snippets
FILLER_WORDS = re.compile(
    r'\b(um+|uh+|ah+|er+)\b',
    re.IGNORECASE
)

CHEVRONS = re.compile(r'>+\s*')

# function to clean the transcripts
def clean_transcript(text):
    # remove speaker chevrons
    text = CHEVRONS.sub('', text)

    # normalize whitespace / newlines
    text = text.replace('\n', ' ')
    text = re.sub(r'\s{2,}', ' ', text)

    # remove filler words
    text = FILLER_WORDS.sub('', text)

    # clean up double spaces
    text = re.sub(r'\s{2,}', ' ', text)

    return text.strip()

# function to asynchronously get trnascripts and clean
def fetch_transript(channel_id, vidx, vid_id):
    result = {
        'channel_id': channel_id,
        'video_index': vidx,
        'video_id': vid_id,
        'status': 'unknown',
        'message': '',
        'filename': None
    }

    # create the json file for the transcript
    filename = f"{folder_path_pathlib}/{channel_id}_transcript_{vidx + 1}.json"
    result[filename] = str(filename)

    # implement jitter to stagger the threads so they won't all fire at once (triggering YouTube blocking/soft bans)
    time.sleep(random.uniform(0, JITTER_MAX))

    # attempt to call/request transcript up to MAX_RETRIES
    for attempt in range(1, MAX_RETRIES + 1):
        # Execute request for vid_captions
        try:
            # get the transcript
            transcript_list = ytt_api.list(vid_id)
            transcript = transcript_list.find_transcript(['en'])

            raw_snippets = transcript.fetch()

            if not raw_snippets:
                result['status'] = 'warning'
                result['message'] = f"No transcript content found for video {vid_id}"
                return result

            # for each snippet of text in the transcript clean the text and, with the start and duration, to a cleaned_transcript_snippets array
            cleaned_transcript_snippets = []
            for snippet in raw_snippets:
                cleaned_text = clean_transcript(snippet.text)

                if cleaned_text:
                    cleaned_transcript_snippets.append({'text': cleaned_text, 'start': snippet.start, 'duration': snippet.duration})

            if not cleaned_transcript_snippets:
                result['status'] = 'warning'
                result['message'] = f"No valid snippets after cleaning for video {vid_id}"

            try:
                with open(filename, 'w') as json_file:
                    json.dump(cleaned_transcript_snippets, json_file, indent=4)

                # call the function to chunk the transcript
                # by default is 500 tokens and 50 token overlaps
                chunk_result = read_and_chunk_transcript(filename)

                result['status'] = 'success'
                result['message'] = f'Successfully wrote transcript and chunked to {filename}. {chunk_result}'
                return result

            except IOError as e:
                result['status'] = 'error'
                result['message'] = f"Error with writing to json file {filename}: {e}"
                return result

        # non-retryable errors/excepts
        except TranscriptsDisabled:
            result['status'] = 'skip'
            result['message'] = f"Transcripts disabled for video {vid_id}"
            return result

        except NoTranscriptFound:
            result['status'] = 'skip'
            result['message'] = f"No English transcript found for video {vid_id}"
            return result

        except VideoUnavailable:
            result['status'] = 'skip'
            result['message'] = f"Video {vid_id} is unavailable (may be private/deleted)"
            return result

        except (NotTranslatable, TranslationLanguageNotAvailable):
            result['status'] = 'skip'
            result['message'] = f"Transcript not available/translatable for video {vid_id}"
            return result

        except (CookiePathInvalid, FailedToCreateConsentCookie):
            result['status'] = 'error'
            result['message'] = f"Cookie/authentication error for video {vid_id}: check proxy config"
            return result

        # retryable erros/excepts
        except YouTubeRequestFailed as e:
            if attempt < MAX_RETRIES:
                # calculate waiting time that scales exponential with the attempt count, and has a jitter to mimic human behaviour
                wait = BASE_DELAY * (2 ** (attempt - 1)) + random.uniform(0, JITTER_MAX)

                print(
                    f"[Attempt {attempt}/{MAX_RETRIES}] YouTubeRequestFailed for "
                    f"{vid_id}: {e}. Retrying in {wait:.1f} seconds..."
                )

                time.sleep(wait)
            else:
                result['status'] = 'error'
                result['message'] = f"YouTube request failed for video {vid_id}: {e}"
                return result

        # Generic exceptions (include wait as well)
        except Exception as e:
            if attempt < MAX_RETRIES:
                # calculate waiting time/delay
                wait = BASE_DELAY * (2 ** (attempt - 1)) + random.uniform(0, JITTER_MAX)

                print(
                    f"[Attempt {attempt}/{MAX_RETRIES}] generic Exception for "
                    f"{vid_id}: {e}. Retrying in {wait:.1f} seconds..."
                )

                time.sleep(wait)
            else:
                result['status'] = 'error'
                result['message'] = f"Unexpected error processing video {vid_id}: {type(e).__name__}: {e}"
                return result# read in the list of important channels and their videos on the topic of AI

vid_data = {}
try:
    file_path_pathlib = Path(__file__).parent.parent.parent / 'data' / 'channel_vids.json'

    with open(file_path_pathlib, 'r') as file:
        vid_data = json.load(file)
except FileNotFoundError:
    print("Json file for channels not found")    
    exit(1)

with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    futures = []

    # for each channel and videos in the vid_data, get the transcript of the videos
    for channel_id, vids_list in vid_data.items():
        for vidx, vid_id in enumerate(vids_list):
            future = executor.submit(fetch_transript, channel_id, vidx, vid_id)
            futures.append(future)

    for future in concurrent.futures.as_completed(futures):
        try:
            result = future.result()
            print(result)
        except Exception as exc:
            print(f'{future} generated an exception: {exc}')
