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
    order='viewCount',
    publishedAfter=time_6_months_ago,
    regionCode='US',
    type='video',
    q='AI',
) 

# will get a lot of videos, add them to a list, then find the most prevelant channels from there
# execute the request
try:
    # get the first response and extract the videos and nextPageToken
    search_response = ai_search.execute()
    nextPageToken = search_response.get('nextPageToken')
    vids = search_response.get('items', [])

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
                order='viewCount',
                pageToken= nextPageToken,
                publishedAfter=time_6_months_ago,
                regionCode='US',
                type='video',
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

# then for the vids find the most popular channels
channel_freq_dist = {}
for vid in vids:
    channelId = vid['snippet']['channelId']
    if channelId in channel_freq_dist:
        channel_freq_dist[channelId] += 1
    else:
        channel_freq_dist[channelId] = 1

# sort the values
sort_channel_freq_dist = sorted(channel_freq_dist.items(), key=lambda item: item[1], reverse=True)

# put the top 20 channels into json dict
top_20_channel_dist = list(dict(sort_channel_freq_dist[:20]))
filename = 'data/channels.json'
try:
    with open(filename, 'w') as json_file:
        json.dump(tuple, json_file, indent=4)
except IOError as e:
    print(f"Error with writing to json file: {e}")


# close the service object for YouTube API
youtube.close()