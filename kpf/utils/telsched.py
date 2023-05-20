import requests
import json
from datetime import datetime, timedelta


##-----------------------------------------------------------------------------
## Functions to interact with telescope DB
##-----------------------------------------------------------------------------
def querydb(req):
    '''A simple wrapper to form a generic API level query to the telescope
    schedule web API.  Returns a JSON object with the result of the query.
    '''
    url = f"https://www.keck.hawaii.edu/software/db_api/telSchedule.php?{req}"
    r = requests.get(url)
    return json.loads(r.text)


def get_schedule(date, tel):
    '''Use the querydb function and getSchedule of the telescope schedule web
    API with arguments for date and telescope number.  Returns a JSON object
    with the schedule result.
    '''
    if tel not in [1,2]:
        raise KPFError(f"Telescope number in query must be 1 or 2")
    req = f"cmd=getSchedule&date={date}&telnr={tel}"
    result = querydb(req)
    return result

def when_is_KPF_scheduled(date=None):
    if date is None:
        date = datetime.now().strftime('%Y-%m-%d')
    ut_date = datetime.strptime(date, '%Y-%m-%d') + timedelta(days=1)
    ut_date_str = ut_date.strftime('%Y-%m-%d')
    schedule = get_schedule(date, 1)
    instruments = [s['Instrument'] for s in schedule]
    for s in schedule:
        if s['Instrument'] == 'KPF':
            start_time = datetime.strptime(f"{ut_date_str} {s['StartTime']}", '%Y-%m-%d %H:%M')
            end_time = datetime.strptime(f"{ut_date_str} {s['EndTime']}", '%Y-%m-%d %H:%M')
            print(start_time, end_time)
            print(end_time-start_time)
