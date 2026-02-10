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
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta

# Get the api key and build the service object for YouTube API
youtube_api_key = os.getenv('YOUTUBE_API_KEY')
youtube = build('youtube', 'v3', developerKey=youtube_api_key)

# Create the collections that I may need
# Collections: search, channels, captions, videos, videocategories, comments, etc.
search = youtube.search()
channels = youtube.channels()

# function to get teh rfc 3339 time a certaim amount of months ago
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
    q='AI',
) 

# will get a lot of videos, add them to a list, then find the most prevelant channels from there
# execute the request
vids = []
try:
    # get the first response and extract the videos and nextPageToken
    search_response = ai_search.execute()
    nextPageToken = search_response.get('nextPageToken')
    vids.extend(search_response.get('items', []))

    LIMIT = 20
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
                q='AI',
            )
        else:
            break

        search_response = ai_search.execute()
        nextPageToken = search_response.get('nextPageToken')   
        vids.extend(search_response.get('items', []))
        
        curr_page += 1
except HttpError as e:
    print(f'Error response status code : {e.status_code}, reason : {e.error_details}')

# Remove duplicate channels (get unique channels)
# from there will find the prolific channels
channel = []
for vid in vids:
    channelId = vid['snippet']['channelId']
    if channelId not in channel:
        channel.append(channelId)

# get detailed information on the channels found
# choose the channels with most video count and view count
prolific_channels = {}
for channel_id in channel:
    channel_search = channels.list(
            part='statistics, topicDetails',
            id=channel_id
    )
    
    # execute the request
    try:
        channel_response = channel_search.execute()
        channel_items = channel_response.get('items', [])
        
        if int(channel_items[0]['statistics']['videoCount']) > 100:
            # then add to the dictionary
            prolific_channels[channel_id] = channel_items[0]['statistics']['videoCount']
    except HttpError as e:
        print(f'Error response status code : {e.status_code}, reason : {e.error_details}')

# put the top 20 channels into json dict
prolific_channels = [*prolific_channels]
prolific_channels = prolific_channels[:20]
filename = 'data/channels.json'
try:
    with open(filename, 'w') as json_file:
        json.dump(prolific_channels, json_file, indent=4)
except IOError as e:
    print(f"Error with writing to json file: {e}")


# close the service object for YouTube API
youtube.close()
