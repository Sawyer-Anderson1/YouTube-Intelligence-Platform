# imports:
# os is inprted to access the YouTube API key
# Google API client's build is imported to build the service object, for YouTube API
# HttpError is imported
# concurrent.futures for concurrency
import os
from pathlib import Path
import json
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor

# Get the api key and build the service object for YouTube API
youtube_api_key = os.getenv('YOUTUBE_API_KEY')
youtube = build('youtube', 'v3', developerKey=youtube_api_key)

# Create the collections that I may need
# Collections: search, channels, captions, videos, videocategories, comments, etc.
comment_threads = youtube.commentThreads()

# create a folder for the comments
folder_data_pathlib = Path(__file__).parent.parent.parent / 'data' / 'comments'
os.makedirs(folder_data_pathlib, exist_ok = True)

# read in the video ids
vid_data = {}
try:
    file_path_pathlib = Path(__file__).parent.parent.parent / 'data'/ 'channel_vids.json'

    with open(file_path_pathlib, 'r') as file:
        vid_data = json.load(file)
except FileNotFoundError:
    print("Json file for channels not found")

# terms that should be mentioned in the comments
terms = ['ai', 'artificial intelligence', 'generative ai', 'large language models', 'llms', 'neural networds', 'ai bubble', 'machine learning', 'ml', 'chatgpt', 'agents', 'agentic ai', 'claude', 'gemini', 'moltbook', 'openclaw', 'grok']

# function to perform the comment retrieval
def comment_retrieve(channel_id, vid_id):
    # Create the request list
    comments = comment_threads.list(
        part="snippet",
        videoId=vid_id,
        maxResults=5,
        textFormat='plainText'
    )

    # then execute the the comment_threads retrieval
    try:
        comment_response = comments.execute()

        comment_items = comment_response.get('items', [])
        for comment in comment_items:
            # create the name of the comment
            comment_pathlib = Path(__file__).parent.parent.parent / 'data' / 'comments' / '
    except HttpError as e:
       print(f'Error response status code : {e.status_code}, reason : {e.error_details}')

# run the retrieval concurrently
with ThreadPoolExecutor(max_workers=5) as executor:
    futures = []

    # for each of the video ids for each channel get comment threads
    for channel_id, vids_list in vid_data.items():
        for vidx, vid_id in enumerate(vids_list):
            future = executor.submit(comment_retrieve, channel_id, vid_id)
            futures.append(future)
