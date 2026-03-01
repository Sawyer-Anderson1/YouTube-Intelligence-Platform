from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta

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
