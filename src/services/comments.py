# imports:
# os is inprted to access the YouTube API key
# Google API client's build is imported to build the service object, for YouTube API
# HttpError is imported
# concurrent.futures for concurrency
import os
import re
from pathlib import Path
import json
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor

# import the check for english file
from check_for_english_text import check_english

# Get the api key and build the service object for YouTube API
for var in ('HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'WEBSHARE_PROXY_USER', 'WEBSHARE_PROXY_PASSWORD'):
    os.environ.pop(var, None)

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
def comment_retrieve(vid_id):
    # Create the request list
    comments = comment_threads.list(
        part="snippet",
        videoId=vid_id,
        maxResults=5,
        textFormat='plainText'
    )

    # create the name of the comment
    vid_comments_pathlib = folder_data_pathlib / f"{vid_id}_comments.json"

    # list to put comment dicts in 
    relevant_comments = []

    # then execute the the comment_threads retrieval
    try:
        comment_response = comments.execute()

        comment_items = comment_response.get('items', [])
        for comment in comment_items:
            top_comment_id = comment['snippet']['topLevelComment']['id']

            # parse the top comment
            top_comment = comment['snippet']['topLevelComment']

            # get data
            comment_text = top_comment['snippet']['textDisplay']
            comment_author = top_comment['snippet']['authorDisplayName']
            comment_likes = top_comment['snippet']['likeCount']
            comment_publishedAt = top_comment['snippet']['publishedAt']

            # check if the comment is english and if it contains the category related terms (not off topic)
            # call the external function
            is_english_comment = check_english(comment_text)

            term_pattern = re.compile(r'\b(?:' + '|'.join(terms) + r')\b', re.IGNORECASE)
            if term_pattern.search(comment_text) and is_english_comment:
                # format data in dictionary
                comment_data = {
                    'commentId': top_comment_id,
                    'author': comment_author,
                    'text': comment_text,
                    'likes': comment_likes,
                    'published_at': comment_publishedAt
                }

                # append comment data to list of relevant comments
                relevant_comments.append(comment_data)

        # then write to comment folder
        try:
            with open(vid_comments_pathlib, 'w') as json_file:
                json.dump(relevant_comments, json_file, indent=4)

        except IOError as e:
            print(f"Error writing json file: {e}")

    except HttpError as e:
       print(f'Error response status code : {e.status_code}, reason : {e.error_details}')

# run the retrieval concurrently
with ThreadPoolExecutor(max_workers=5) as executor:
    futures = []

    # for each of the video ids for each channel get comment threads
    for channel_id, vids_list in vid_data.items():
        for vidx, vid_id in enumerate(vids_list):
            future = executor.submit(comment_retrieve, vid_id)
            futures.append(future)

    for future in concurrent.futures.as_completed(futures):
        try:
            future.result()
        except Exception as e:
            print(f"Exception in concurrency thread retrieving comments: {e}")
