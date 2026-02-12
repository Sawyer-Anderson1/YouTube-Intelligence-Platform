# imports:
# os is inprted to access the YouTube API key
# the youtube transcript api is imported to get the transcripts
# import the proxy config for webshare, to be able to rotate proxies and access the transcripts
# import nltk and text processing libraries (wordninja for word segmentation)
import os
import json
from pathlib import Path
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import WebshareProxyConfig

import nltk
import wordninja

# get the webshare proxy information
WEBSHARE_PROXY_USER = os.getenv('WEBSHARE_PROXY_USER')
WEBSHARE_PROXY_PASSWORD = os.getenv('WEBSHARE_PROXY_PASSWORD')

# read in the YouTubeTranscriptApi
ytt_api = YouTubeTranscriptApi(
    proxy_config=WebshareProxyConfig(
        proxy_username=str(WEBSHARE_PROXY_USER),
        proxy_password=str(WEBSHARE_PROXY_PASSWORD),
    )
)

# function to clean the transcripts
def clean_transcript(text):
    # fix any weird word segmentation
    segmented_string = " ".join(wordninja.split(text))

    # correcting spelling, first tokenize and do not lower text (since the case can provide meaning to the LLMs)
    word_tokens = segmented_string.split()

    # get list of english words
    en_words = nltk.corpus.words.words()

    corrected_tokens = []
    for token in word_tokens:
        # find word with lowest distance and replace
        corrected_token = min(en_words, key=lambda x: nltk.edit_distance(x, token))
        corrected_tokens.append(corrected_token)

    return " ".join(corrected_tokens)

# read in the list of important channels and their videos on the topic of AI
vid_data = {}
try:
    file_path_pathlib = Path(__file__).parent.parent.parent / 'data' / 'channel_vids.json'

    with open(file_path_pathlib, 'r') as file:
        vid_data = json.load(file)
except FileNotFoundError:
    print("Json file for channels not found")    

# for each channel and videos in the vid_data, get the transcript of the videos
for channel_id, vids_list in vid_data.items():
    for vidx, vid_id in enumerate(vids_list):
        # Execute request for vid_captions
        try:
            # create the json file for the transcript
            filename = f"data/transcripts/{channel_id}_transcript_{vidx + 1}.json"

            # get the transcript
            fetched_transcript = ytt_api.fetch(vid_id)

            # for each snippet of text in the transcript clean the text and, with the start and duration, to a cleaned_transcript_snippets array
            cleaned_transcript_snippets = []
            for snippet in fetched_transcript:
                cleaned_text = clean_transcript(snippet.text)
                cleaned_transcript_snippets.append({'text': cleaned_text, 'start': snippet.start, 'duration': snippet.duration})

            try:
                with open(filename, 'w') as json_file:
                    json.dump(cleaned_transcript_snippets, json_file, indent=4)
            except IOError as e:
                print(f"Error with writing to json file: {e}")

        except Exception as e:
            # this error is probably for the region restrictions or captions availability
            # do not create a transcript .json file for it, just continue
            continue
