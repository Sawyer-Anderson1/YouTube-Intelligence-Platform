# imports:
# os is inprted to access the YouTube API key
# Google API client's build is imported to build the service object, for YouTube API
# HttpError is imported
# ...
import os
import json
from pathlib import Path
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta

# get the youtube api key and build the service object for the youtube api calls
youtube_api_key = os.getenv('YOUTUBE_API_KEY')
youtube = build('youtube', 'v3', developerKey=youtube_api_key)

# Create the collection(s) I need:
channels = youtube.channels()
playlist_items = youtube.playlistItems()
videos = youtube.videos()

# function to get the rfc 3339 time a certaim amount of months ago
def get_time_months_ago_rfc3339(months_ago: int) -> str:
    '''
    Docstring for get_time_months_ago_rfc3339
    
    :param months_ago: the amount of months that we are going back to get the time for
    :type months_ago: int
    :return: the time a certain amount of months ago
    :rtype: str of RFC 3339 datetime
    '''
    
    current_utc = datetime.now(timezone.utc)
    past_time = current_utc - relativedelta(months=months_ago)
    rfc3339_utc_str = past_time.isoformat().replace('+00:00', 'Z')
    return rfc3339_utc_str

# function to check a video from a chennel's uploads playlist for date (within 6 months), contentc, etc.
def check_vids(upload_items):
    # get the month time 6 months ago
    time_6_months_ago = get_time_months_ago_rfc3339(6)

    # list with acceptable terms on the topic of AI
    terms = ['ai', 'artificial intelligence', 'generative ai', 'large language models', 'llms', 'neural networds', 'ai bubble', 'machine learning', 'ml', 'chatgpt', 'agents', 'agentic ai']
    # iterate through the items and do the checks
    vids_filtered = []
    for vid in upload_items:
        # only get videos with privacy status public
        if vid['status']['privacyStatus'] == 'public':
            # check if the current vid is at past limit
            if str(vid['contentDetails']['videoPublishedAt']) == time_6_months_ago:
                return vids_filtered, True

            # else continue and check for relevant vids
            # get title and description and lower case for checking for terms
            title = vid['snippet']['title']
            description = vid['snippet']['description']

            # also check for view count > 5k, if captions are enabled/allowed for video, and the region restrictions allow US
            video_list = videos.list(
                part='statistics, contentDetails',
                id=vid['contentDetails']['videoId']
            )
            video = video_list.execute()
            video_item = video.get('items', [])

            if (any(term in title for term in terms) or any(term in description for term in terms)) and int(video_item[0]['statistics']['viewCount']) > 5000 and video_item[0]['contentDetails']['caption'] == 'true' and ('US' in video_item[0]['contentDetails']['regionRestriction'].get('allowed', [])):
                # then add video id to list
                vids_filtered.append(video_item[0]['id'])
    return vids_filtered, False

# read in the list of important channels on the topic of AI
try:
    file_path_pathlib = Path(__file__).parent.parent.parent / 'data' / 'channels.json'

    with open(file_path_pathlib, 'r') as file:
        data = json.load(file)
    
    # Call the request for channel list
    # save a dictionary for each channel's uploads playlist
    channel_uploads = {}
    for id in data:
        channel = channels.list(
                part="contentDetails",
                id=id
        )

        # Execute request for channel playlists
        try:
            channel_response = channel.execute()

            # get the uploads playlist id
            uploads_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            channel_uploads[id] = uploads_id
        except HttpError as e:
            print(f'Error response status code : {e.status_code}, reason : {e.error_details}')
    
    # using the uploads playlist, get the videos from the playlist
    for channel, upload_id in channel_uploads.items():
        items = playlist_items.list(
            part='contentDetails, snippet, status',
            playlistId=upload_id,
            maxResults=25
        )

        # execute the request
        channels_vids = []
        try:
            playlist_response = items.execute()

            # get the nextPageToken and uploads videos/items
            nextPageToken = playlist_response.get('nextPageToken')
            playlist_item = playlist_response.get('items', [])

            # run the items through the check, and return the items we'll keep (the relevant ones to the topic)
            filtered_vids, MONTH_LIMIT_FLAG = check_vids(playlist_item)
            channels_vids.extend(filtered_vids)

            # then do pagination till the check_vids has elements that went to 6 months ago or there are no more nextPageTokens
            # also add a limit to not keep so much vids from just one channel
            VID_PER_CHANNEL = 75
            while True and len(channels_vids) <= VID_PER_CHANNEL:
                if nextPageToken != None and MONTH_LIMIT_FLAG != True:
                    items = playlist_items.list(
                        part='contentDetails, snippet, status',
                        playlistId=upload_id,
                        pageToken=nextPageToken,
                        maxResults=25
                    )
                else:
                    break

                playlist_response = items.execute()
                nextPageToken = playlist_response.get('nextPageToken')
                playlist_item = playlist_response.get('items', [])

                # then check the vids for the category if within month limit
                filtered_vids,MONTH_LIMIT_FLAG = check_vids(playlist_item)
                channels_vids.extend(filtered_vids)
        except HttpError as e:
            print(f'Error response status code : {e.status_code}, reason : {e.error_details}')

        # then add the video id list for a specific channel to the channel_uploads dictionary
        channel_uploads[channel] = channels_vids

    # we have the relevant videos for our set of channels
    # then export to json
    filename = "data/channel_vids.json"
    try:
        with open(filename, 'w') as json_file:
            json.dump(channel_uploads, json_file, indent=4)
    except IOError as e:
        print(f"Error with writing to json file: {e}")

except FileNotFoundError:
    print("Json file for channels not found")

# close the youtube api
youtube.close()
