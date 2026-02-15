# imports:
# os is inprted to access the YouTube API key
# the youtube transcript api is imported to get the transcripts
# import the proxy config for webshare, to be able to rotate proxies and access the transcripts
# spellchecker for spell checking
import os
import json
from pathlib import Path
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor

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

from spellchecker import SpellChecker

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

# spell checker instance
spell_check = SpellChecker()

# function to clean the transcripts
def clean_transcript(text):
    # correcting spelling, first tokenize and do not lower text (since the case can provide meaning to the LLMs)
    # fix any weird word segmentation
    tokens = text.split()

    if not tokens:
        return ""

    misspelled_tokens = spell_check.unknown(tokens)

    corrected_tokens = []
    for token in tokens:
        if token in misspelled_tokens:
            correction = spell_check.correction(token)
            corrected_tokens.append(correction if correction is not None else token)
        else:
            corrected_tokens.append(token)

    return " ".join(corrected_tokens)

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
    filename = f"{folder_path_pathlib}\\{channel_id}_transcript_{vidx + 1}.json"
    result[filename] = str(filename)

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

            result['status'] = 'success'
            result['message'] = f'Successfully wrote transcript to {filename}'
            return result

        except IOError as e:
            result['status'] = 'error'
            result['message'] = f"Error with writing to json file {filename}: {e}"
            return result
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

    except YouTubeRequestFailed as e:
        result['status'] = 'error'
        result['message'] = f"YouTube request failed for video {vid_id}: {e}"
        return result

    # Generic exceptions
    except Exception as e:
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

with ThreadPoolExecutor(max_workers=25) as executor:
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
