import os
import sys
import time
import datetime
import json
import requests
import urllib3
urllib3.disable_warnings() # We're going to do verify=False, so ignore warnings
import numpy as np

import ktl
import keygrabber

from kpf import log, cfg
from kpf.ObservingBlocks.ObservingBlock import ObservingBlock
from kpf.observatoryAPIs.schedule import get_semester_dates


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
## query_KPFCC_API
##-------------------------------------------------------------------------
def query_KPFCC_API(query, params):
    url = cfg.get('Database', 'url')
    log.debug(f"Running database query: {url}{query}")
    log.debug(params)
    if 'hash' not in params.keys():
        params['hash'] = os.getenv('APIHASH', default='')
    r = requests.post(f"{url}{query}", json=params, verify=False)
    # Try to parse result as json
    try:
        result = json.loads(r.text)
        log.debug(f'{query} retrieved {len(result)} results')
    except Exception as e:
        log.error(f'Failed to parse result:')
        log.error(r.text)
        log.error(e)
        result = None
    # Check for error in the parsed result
    if type(result) == dict:
        success = result.get('success', None)
        if success == 'ERROR':
            log.error('success: {success}')
            msg = result.get('message', None)
            if msg: log.error('Message: {msg}')
            details = result.get('details', None)
            if details: log.error('Details: {details}')
            result = None
    return result


def get_OBs_from_KPFCC_API(params):
    result = query_KPFCC_API('getKPFObservingBlock', params)
    if result is None:
        return []
    OBs = []
    n = len(result)
    for i,entry in enumerate(result):
        try:
            log.debug(f'Parsing entry {i+1} of {n}')
#             log.debug(entry)
            OB = ObservingBlock(entry)
        except Exception as e:
            log.error(f'  Unable to parse entry {i+1} in to an ObservingBlock')
            log.error(f'  {e}')
            log.debug(f'  OB ID = {entry.get("id")}')
        else:
            if OB.validate():
                log.debug(f'  OB {i+1} is valid')
                OBs.append(OB)
            else:
                log.warning(f'  OB {i+1} is invalid')
                if OB.Target is not None:
                    for line in OB.Target.to_lines(comment=True):
                        if line.find('ERR') > 0:
                            log.debug(line)
                for obs in OB.Observations:
                    for line in obs.to_lines(comment=True):
                        if line.find('ERR') > 0:
                            log.debug(line)

    log.debug(f'get_OBs_from_database parsed {len(OBs)} ObservingBlocks')
    return OBs
