from datetime import datetime
from tzlocal import get_localzone

def get_scraped_time():
    local_tz = get_localzone()
    now = datetime.now(local_tz)
    return now.isoformat()