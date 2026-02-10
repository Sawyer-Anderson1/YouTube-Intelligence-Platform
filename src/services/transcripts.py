# imports:
# os is inprted to access the YouTube API key
# the youtube transcript api is imported to get the transcripts
# import the proxy config for webshare, to be able to rotate proxies and access the transcripts
import os
import json
from pathlib import Path
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import WebshareProxyConfig

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
            fetched_transcript = ytt_api.fetch(vid_id)

            full_transcript_text = ""
            for snippet in fetched_transcript:
                full_transcript_text += " " + snippet.text
            vids_list[vidx] = full_transcript_text
        except Exception as e:
            # we set the transcript to blank to be easily parsed out
            vids_list[vidx] = ""
        vids_list[vidx]
        cleaned_transcript = vids_list[vidx].replace(">>", "").replace("\n", " ").replace("\\'", "'").replace("\'", "").replace("\t", " ")
        vids_list[vidx] = cleaned_transcript.lower()
    vid_data[channel_id] = vids_list

filename = "data/vids_transcripts.json"
try:
    with open(filename, 'w') as json_file:
        json.dump(vid_data, json_file, indent=4)
except IOError as e:
    print(f"Error with writing to json file: {e}")
