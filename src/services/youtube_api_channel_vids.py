# imports:
# os is inprted to access the YouTube API key
# Google API client's build is imported to build the service object, for YouTube API
# HttpError is imported
# imports to calculate the time 6 months ago
# and import to detect language
import os
import json
from pathlib import Path
import re

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# import external function to check for english text
from check_for_english_text import check_english

# import another external function to get time 6 months ago
from get_time import get_time_months_ago_rfc3339

# --------------------------------------
#  Get YouTubeAPI API, Build, and
#  Collections
# --------------------------------------

# get the youtube api key and build the service object for the youtube api calls
youtube_api_key = os.getenv('YOUTUBE_API_KEY')
youtube = build('youtube', 'v3', developerKey=youtube_api_key)

# Create the collection(s) I need:
channels = youtube.channels()
playlist_items = youtube.playlistItems()
videos = youtube.videos()

# ---------------------------------------------
#  Function to Check For Relevant Videos,
#  and Save MetaData
# ---------------------------------------------

# function to check a video from a chennel's uploads playlist for date (within 6 months), contentc, etc.
def check_vids(upload_items):
    # get the month time 6 months ago
    time_6_months_ago = get_time_months_ago_rfc3339(6)

    # list with acceptable terms on the topic of AI
    terms = ['ai', 'artificial intelligence', 'generative ai', 'large language models', 'llms', 'neural networds', 'ai bubble', 'machine learning', 'ml', 'chatgpt', 'agents', 'agentic ai', 'claude', 'gemini', 'moltbook', 'openclaw', 'grok']

    # the final array of fully filtered/checked vids
    vids_filtered = []

    # make the video id array for the uploads and prefilter for the information available in the playlistItem
    prefiltered_vid_ids = []
    hit_6_month_limit = False

    for vid in upload_items:
        # only get videos with privacy status public
        if vid['status']['privacyStatus'] == 'public':
            # check if the current vid is at past limit
            if vid['contentDetails']['videoPublishedAt'] <= time_6_months_ago:
                hit_6_month_limit = True
                break

            # else continue and check for relevant vids
            # get title and description and lower case for checking for terms
            title = vid['snippet'].get('title', '').lower()
            description = vid['snippet'].get('description', '').lower()

            # call external function to check
            is_english_title = check_english(title)
            is_english_description = check_english(title)
            is_english_video = (is_english_title and is_english_description)

            term_pattern = re.compile(r'\b(?:' + '|'.join(terms) + r')\b', re.IGNORECASE)
            if term_pattern.search(title) and term_pattern.search(description) and is_english_video:
                prefiltered_vid_ids.append(vid['contentDetails']['videoId'])

    # make the videos list request much more efficient by adding a list of video ids
    if not prefiltered_vid_ids:
        return vids_filtered, hit_6_month_limit

    video_list = videos.list(
        part='snippet, statistics, contentDetails',
        id=prefiltered_vid_ids
    )

    # exectue request
    try:
        video = video_list.execute()
        video_items = video.get('items', [])

        # iterate through the video ids and do the rest of the checks
        for item_id in range(len(video_items)):
            view_count = int(video_items[item_id]['statistics']['viewCount'])

            # ------------------------------------------
            #  Save Video Metrics for Metadata
            # ------------------------------------------

            video_metrics[video_items[item_id]['id']] = {
                "channel_id": channel,
                "title": video_items[item_id]['snippet']['title'],
                "published_at": video_items[item_id]["snippet"]["publishedAt"],
                "view_count": view_count,
                "like_count": int(video_items[item_id]['statistics'].get('likeCount', 0)),
                "comment_count": int(video_items[item_id]['statistics'].get('commentCount', 0)),
                "duration": video_items[item_id]['contentDetails']['duration']
            }

            # check if video is in English using defaultLanguage or defaultAudioLanguage
            default_language = video_items[item_id]['snippet'].get('defaultLanguage', '')
            default_audio_language = video_items[item_id]['snippet'].get('defaultAudioLanguage', '')
            is_english_video_or_not_set = (default_language == 'en' or default_audio_language == 'en-US' or default_language == '' or default_audio_language == '')

            if view_count > 5000 and is_english_video_or_not_set:
                # get the region restriction dict if available
                region_restriction = video_items[item_id]['contentDetails'].get('regionRestriction', {})

                # then if there are region restrictions check if the proxy server's countries are all in the allowed array
                if region_restriction != {}:
                    if 'US' in region_restriction.get('allowed', []):
                        # then add video id to list
                        vids_filtered.append(video_items[item_id]['id'])
                else:
                    vids_filtered.append(video_items[item_id]['id'])

        # return filtered list
        return vids_filtered, hit_6_month_limit
    except HttpError as e:
        print(f'Error response status code : {e.status_code}, reason : {e.error_details}')

    # return the final filtered list
    return vids_filtered, hit_6_month_limit

# ------------------------------------------------------------------------------------
#  Read the Channels, Get Channel Uploads Playlist, and Check Vids from Playlists
# ------------------------------------------------------------------------------------

# read in the list of important channels on the topic of AI
try:
    file_path_pathlib = Path(__file__).parent.parent.parent / 'data' / 'channels.json'

    with open(file_path_pathlib, 'r') as file:
        channel_ids = json.load(file)

    # Call the request for channel list
    # save a dictionary for each channel's uploads playlist
    channel_uploads = {}

    # save a dictionary for the video metrics
    video_metrics = {}

    # -----------------------------------------------------
    #  Retrieve Channel Info and Retrieve Uploads Playlist
    # -----------------------------------------------------

    # have entire channel_ids in singular channels.list call to make it much more efficient
    # but since there is a limit of 50 ids per .list request create a list of them in a for statement
    channel_lists = []
    if len(channel_ids) >= 50:
        for i in range(0, len(channel_ids), 50):
            channel = channels.list(
                        part="snippet, contentDetails",
                        id=channel_ids[i:i+50]
            )
            # add the current channel.list to channel_lists array
            channel_lists.append(channel)
    else:
        channel = channels.list(
            part="snippet, contentDetails",
            id=channel_ids
        )
        channel_lists.append(channel)

    # Execute requests for channel playlists
    try:
        channel_items = []
        for i in range(len(channel_lists)):
            channel_response = channel_lists[i].execute()
            channel_item = channel_response.get('items', [])

            # then extend the current list of items for the response to the collective channel_items array
            channel_items.extend(channel_item)

        channel_map = {} # to map the item['id'] or the upload id
        for item in channel_items:
            channel_id = item['id']

            # check for the snippet.defaultLanguage is english and (maybe) snippet.country
            default_language = item['snippet'].get('defaultLanguage', '')
            if default_language == 'en':
                # get the uploads playlist id
                uploads_id = item['contentDetails']['relatedPlaylists']['uploads']
                channel_uploads[channel_id] = uploads_id
            elif default_language == '':
                # get the uploads playlist id
                uploads_id = item['contentDetails']['relatedPlaylists']['uploads']
                channel_uploads[channel_id] = uploads_id
    except HttpError as e:
            print(f'Error response status code : {e.status_code}, reason : {e.error_details}')

    # ---------------------------------------------------
    #  Go Through Uploads Playlist for Each Channel,
    #  Check the Vids and Save Relevant Vids
    # ---------------------------------------------------

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
            VID_PER_CHANNEL = 50
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

                try:
                    playlist_response = items.execute()
                    nextPageToken = playlist_response.get('nextPageToken')
                    playlist_item = playlist_response.get('items', [])

                    # then check the vids for the category if within month limit
                    filtered_vids, MONTH_LIMIT_FLAG = check_vids(playlist_item)
                    channels_vids.extend(filtered_vids)
                except HttpError as e:
                    print(f'Error response status code : {e.status_code}, reason : {e.error_details}')
            # then add the video id list for a specific channel to the channel_uploads dictionary
            channel_uploads[channel] = channels_vids
        except HttpError as e:
            print(f'Error response status code : {e.status_code}, reason : {e.error_details}')

    # we have the relevant videos for our set of channels
    # then choose the top channels from there
    channel_uploads = dict(sorted(channel_uploads.items(), key=lambda x: len(x[1]), reverse=True))

    # ------------------------------------------
    #  Keep up to 20 Most Relevant Channels,
    #  with Most Vids on Topic
    # ------------------------------------------

    # get up to 1500 videos or up to 20 channels
    MAX_VIDS = 1500
    MAX_CHANNELS = 20

    vids_count = 0
    channel_key_index = list(channel_uploads.keys())
    curr_index = 0
    selected_channels_vids = {}
    while len(selected_channels_vids) < MAX_CHANNELS and vids_count < MAX_VIDS and curr_index < len(channel_key_index):
        if channel_uploads[channel_key_index[curr_index]] != []:
            selected_channels_vids[channel_key_index[curr_index]] = channel_uploads[channel_key_index[curr_index]]
            vids_count += len(channel_uploads[channel_key_index[curr_index]])
        curr_index += 1

    # -------------------------------------
    #  Save to JSON (channel_vids.json)
    # -------------------------------------

    # then export to json
    filename = "data/channel_vids.json"
    try:
        with open(filename, 'w') as json_file:
            json.dump(selected_channels_vids, json_file, indent=4)
    except IOError as e:
        print(f"Error with writing selected channel vids to json file: {e}")

    # --------------------------------------
    #  Save MetaData/Video Metrics to JSON
    # --------------------------------------

    try:
        with open('data/video_metrices.json', 'w') as file:
            json.dump(video_metrics, file, indent=4)
    except IOError as e:
        print(f"Error with writing video metrics to json file: {e}")

except FileNotFoundError:
    print("Json file for channels not found")

# close the youtube api
youtube.close()
