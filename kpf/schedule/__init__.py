import requests
import json

from kpf import log, cfg


def getSchedule(date='2025-02-01', numdays=1, telnr=1, instrument='KPF', **kwargs):
    # https://vm-appserver.keck.hawaii.edu/api/schedule/getSchedule?date=2025-04-11&numdays=30&instrument=KPF-CC
    url = 'https://vm-appserver.keck.hawaii.edu/api/schedule/'
    query = 'getSchedule'
    params = {'date': date,
              'numdays': numdays,
              'telnr': telnr,
              'instrument': instrument}
    log.debug(f"Running schedule query at {url}{query} with params:")
    log.debug(params)
    r = requests.get(f"{url}{query}", params=params)
    try:
        result = json.loads(r.text)
    except Exception as e:
        log.error(f'Failed to parse result:')
        log.error(r.text)
        log.error(e)
        result = None
    return result
