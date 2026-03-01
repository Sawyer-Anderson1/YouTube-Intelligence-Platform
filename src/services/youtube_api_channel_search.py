# imports:
# os is inprted to access the YouTube API key
# Google API client's build is imported to build the service object, for YouTube API
# HttpError is imported
# datetime and timezone imported to get the current date to dynamically calculate and get results within a certain timeframe
# ...
import os
import json
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# import external function to get time six months ago
from get_time import get_time_months_ago_rfc3339

# --------------------------------------
#  Get YouTubeAPI API, Build, and
#  Collections
# --------------------------------------

# Get the api key and build the service object for YouTube API
youtube_api_key = os.getenv('YOUTUBE_API_KEY')
youtube = build('youtube', 'v3', developerKey=youtube_api_key)

# Create the collections that I may need
# Collections: search, channels, captions, videos, videocategories, comments, etc.
search = youtube.search()
channels = youtube.channels()

# ---------------------------------------------------
#  Perform Search with Query of Future of AI,
#  to get Channel Ids of Channels with Relevant Vids
# ---------------------------------------------------

# On the topic of AI
# Call the request for search
time_6_months_ago = get_time_months_ago_rfc3339(6)
ai_search = search.list(
    part='snippet',
    maxResults=25,
    publishedAfter=time_6_months_ago,
    regionCode='US',
    type='video',
    videoCategoryId = '28',
    relevanceLanguage = 'en',
    q='Future of AI',
) 

# will get a lot of videos, add them to a list, then find the most prevelant channels from there
# execute the request
vids = []
try:
    # get the first response and extract the videos and nextPageToken
    search_response = ai_search.execute()
    nextPageToken = search_response.get('nextPageToken')
    vids.extend(search_response.get('items', []))

    LIMIT = 25
    curr_page = 1
    while True:
        # add limit to pagination
        if curr_page == LIMIT:
            break

        if nextPageToken != None:
            ai_search = search.list(
                part='snippet',
                maxResults=25,
                pageToken= nextPageToken,
                publishedAfter=time_6_months_ago,
                regionCode='US',
                type='video',
                videoCategoryId = '28',
                relevanceLanguage = 'en',
                q='Future of AI',
            )
        else:
            break

        search_response = ai_search.execute()
        nextPageToken = search_response.get('nextPageToken')   
        vids.extend(search_response.get('items', []))

        curr_page += 1
except HttpError as e:
    print(f'Error response status code : {e.status_code}, reason : {e.error_details}')

# ------------------------------------------------------
#  Get Channel Ids of Publisher of Vids Found in Search
# ------------------------------------------------------

# Remove duplicate channels (get unique channels)
# from there will find the prolific channels
channel = []
for vid in vids:
    channelId = vid['snippet']['channelId']
    if channelId not in channel:
        channel.append(channelId)

# ------------------------------------------
#  Save to JSON (channels.json)
# ------------------------------------------

# put then put channels into json dict ordered by video count (will narrow down to 10-20 channels after getting the video ids after filtering)
filename = 'data/channels.json'
try:
    with open(filename, 'w') as json_file:
        json.dump(channel, json_file, indent=4)
except IOError as e:
    print(f"Error with writing to json file: {e}")

# close the service object for YouTube API
youtube.close()
