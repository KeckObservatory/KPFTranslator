import requests
import json


##-----------------------------------------------------------------------------
## Functions to interact with telescope DB
##-----------------------------------------------------------------------------
def get_schedule(date, tel=1, instrument='KPF'):
    url = 'https://vm-appserver.keck.hawaii.edu/api/schedule/getSchedule'
    req = f"date={date}&telnr={tel}&instrument={instrument}"
    r = requests.get(f'{url}?{req}')
    return json.loads(r.text)
