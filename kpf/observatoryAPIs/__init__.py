import os
import copy
import datetime
import json
import requests
import urllib3
urllib3.disable_warnings() # We're going to do verify=False, so ignore warnings

import numpy as np

from kpf import log, cfg
from kpf.ObservingBlocks.ObservingBlock import ObservingBlock


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


def round_microseconds(ut, ndecimals=2):
    '''Round the given date time object to the given decimal seconds.
    '''
    factor = 10**(6-ndecimals)
    new_ms = int(np.round(ut.microsecond/factor)*factor)
    if new_ms == 1000000:
        add_this = 5*10**(-1-ndecimals)
        dt = datetime.timedelta(seconds=add_this)
        rounded = round_microseconds(ut+dt, ndecimals=ndecimals)
    else:
        rounded = ut.replace(microsecond=new_ms)
    return rounded


def truncate_isoformat(ut, ndecimals=2):
    '''Truncate the string carefully since a simple [-4] assumes the all
    microseconds have been printed, which is not the case always.
    '''
    if ut.microsecond == 0:
        output = f"{ut.isoformat()}."
        for i in range(ndecimals):
            output += '0'
    else:
        output = ut.isoformat()[:-4]
    assert len(output) == 22
    return output


##-------------------------------------------------------------------------
## query_observatoryAPI
##-------------------------------------------------------------------------
def query_observatoryAPI(api, query, params, post=False):
    if api == 'proposal' and 'hash' not in params.keys():
        hashenv = os.getenv('APIHASH', default=None)
        if hashenv is None:
            log.error('Unable to read environment variable APIHASH, retrying.')
            hashenv = os.getenv('APIHASH', default=None)
            if hashenv is None:
                log.error('Unable to read environment variable APIHASH')
        else:
            params['hash'] = hashenv
    url = cfg.get('ObservatoryAPIs', f'{api}_url')
    log.debug(f"Running {api} API query: {url}{query}")
    log.debug(f"  Input params: {params}")
    if post == False:
        r = requests.get(f"{url}{query}", params=params)
    else:
        log.debug('Using POST')
        r = requests.post(f"{url}{query}", json=params, verify=False)
    try:
        result = json.loads(r.text)
        log.debug(f"  Query result: {result}")
        if type(result) == dict:
            if result.get('status', '') == 'ERROR':
                message = result.get('message', '')
                details = result.get('details', '')
                log.error(f'Query Failed: {message}')
                log.error(f'  Details: {details}')
    except Exception as e:
        log.error(f'Failed to parse result:')
        log.error(r.text)
        log.error(e)
        result = None
    return result


##-------------------------------------------------------------------------
## A few specific queries
##-------------------------------------------------------------------------
def getPI(semid):
    return query_observatoryAPI('proposal', 'getPI', {'semid': semid})


def getObserverInfo(observerID):
    return query_observatoryAPI('schedule', 'getObserverInfo', {'obsid': observerID})


def addObservingBlockHistory(history):
    return query_observatoryAPI('proposal', 'addObservingBlockHistory', history, post=True)


def getObservingBlockHistory(utdate=None):
    if utdate in [None, 'today']:
        utdate = datetime.datetime.utcnow().strftime('%Y-%m-%d')
    result = query_observatoryAPI('proposal', 'getObservingBlockHistory',
                                  {"utdate": utdate})
    return result.get('history', [])


def setKPFJunkValue(OBid, timestamp, junk=True):
    params = {"id": OBid,
              "timestamp": timestamp,
              "value": str(junk)}
    return query_observatoryAPI('proposal', 'setKPFJunkValue', params, post=True)


def get_OBs_from_KPFCC_API(params):
    result = query_observatoryAPI('proposal', 'getKPFObservingBlock', params)
    if result is None:
        return []
    OBs = []
    failures = []
    invalid = []
    n = len(result)
    for i,entry in enumerate(result):
        log.debug(f'Parsing entry {i+1} of {n}')
        if not isinstance(entry, dict):
            failures.append([f'{entry}', 'Entry is not dict'])
        else:
            status = entry.get('status', None)
            OBid = entry.get('id', None)
            if status not in ['OB_FOUND']:
#                 log.error(f"  ID {OBid}: {entry.get('status', 'No status returned')}")
                failures.append([OBid, status])
            else:
                # Parse the result as an OB in dict form
                try:
                    OB = ObservingBlock(entry)
                except Exception as e:
#                     log.error(f'Unable to parse entry {i+1} in to an ObservingBlock')
#                     log.error(entry)
#                     log.error(f'{e}')
                    failures.append([OBid, f'{e}'])
                else:
                    if OB.validate():
#                         log.debug(f'OB {i+1} is valid')
                        OBs.append(OB)
                    else:
#                         log.debug(f'OB {i+1} is invalid')
                        invalid.append([OBid, entry, OB])
#                         if OB.Target is not None:
#                             for line in OB.Target.to_lines(comment=True):
#                                 if line.find('ERR') >= 0:
#                                     log.warning(line)
#                         for obs in OB.Observations:
#                             for line in obs.to_lines(comment=True):
#                                 if line.find('ERR') >= 0:
#                                     log.warning(line)
    log.info(f'API returned {len(result)} entries')
    log.info(f'  Parsed {len(OBs)} OBs from those entries')
    for failure in failures:
        log.error(f"  OB {failure[0]} failed: {failure[1]}")
    for badOB in invalid:
        log.error(f"  OB {badOB[0]} is invalid")
        print(badOB[1])
        print(badOB[2].validate(verbose=True))
    return OBs
