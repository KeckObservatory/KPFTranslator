import requests
import json

import datetime

from kpf import log, cfg


def get_semester_dates(date):
    if isinstance(date, datetime.datetime):
        if date.month == 1:
            semester = f'{date.year-1}B'
            semester_start_str = f'{date.year-1}-08-01 00:00:00'
            semester_end_str = f'{date.year}-01-31 23:59:59'
        elif date.month > 1 and date.month < 8:
            semester = f'{date.year}A'
            semester_start_str = f'{date.year}-02-01 00:00:00'
            semester_end_str = f'{date.year}-07-31 23:59:59'
        else:
            semester = f'{date.year}B'
            semester_start_str = f'{date.year}-08-01 00:00:00'
            semester_end_str = f'{date.year+1}-01-31 23:59:59'
    elif isinstance(date, str):
        year = int(date[:4])
        semester = date
        if semester[-1] == 'A':
            semester_start_str = f'{year}-02-01 00:00:00'
            semester_end_str = f'{year}-07-31 23:59:59'
        elif semester[-1] == 'B':
            semester_start_str = f'{year}-08-01 00:00:00'
            semester_end_str = f'{year+1}-01-31 23:59:59'
    semester_start = datetime.datetime.strptime(semester_start_str, '%Y-%m-%d %H:%M:%S')
    semester_end = datetime.datetime.strptime(semester_end_str, '%Y-%m-%d %H:%M:%S')
    return semester, semester_start, semester_end


def query_schedule_API(query, params):
    '''See https://vm-appserver.keck.hawaii.edu/api/schedule/swagger/#/
    '''
    url = 'https://vm-appserver.keck.hawaii.edu/api/schedule/'
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


def getPI(semid):
    query = 'getPI'
    params = {'semid': semid}
    return query_schedule_API(query, params)


def getObserverInfo(observerID):
    query = 'getObserverInfo'
    params = {'obsid': observerID}
    return query_schedule_API(query, params)
