import requests
import json
from datetime import datetime


##-----------------------------------------------------------------------------
## Functions to interact with telescope DB
##-----------------------------------------------------------------------------
def query_schedule_database(req, www=False):
    '''Query the telescope schedule database using the API provided by SSG. Use
    the www flag to send the request to the soon to be deprecated www server.
    '''
    if www == True:
        url = f"https://www.keck.hawaii.edu/software/db_api/telSchedule.php?"
    else:
        url = 'https://vm-appserver.keck.hawaii.edu/api/schedule/'
    r = requests.get(f'{url}{req}')
    return json.loads(r.text)


def get_schedule(date, tel=1, instrument='KPF'):
    req = f"getSchedule?date={date}&telnr={tel}&instrument={instrument}"
    return query_schedule_database(req)


def get_ToO_programs():
    now = datetime.utcnow()
    if now.month == 1:
        semester = f"{now.year-1}B"
    elif now.month > 1 and now.month <= 7:
        semester = f"{now.year}A"
    else:
        semester = f"{now.year}B"
    req = f"cmd=getToO&semester={semester}"
    result = query_schedule_database(req, www=True)
    project_codes = []
    PIs = []
    for r in result:
        if 'KPF' in r['InstrumentList'].split():
            project_codes.append(r['ProjCode'])
            PIs.append(r['LastName'])
    return project_codes, PIs
