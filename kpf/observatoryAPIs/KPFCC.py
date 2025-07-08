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
    log.debug(f"Running KPFCC API query: {url}{query}")
    log.debug(params)
    if 'hash' not in params.keys():
        params['hash'] = os.getenv('APIHASH', default='')
    r = requests.post(f"{url}{query}", json=params, verify=False)
    # Try to parse result as json
    try:
        result = json.loads(r.text)
    except Exception as e:
        log.error(f'Failed to parse result as JSON:')
        log.error(r.text)
        log.error(e)
        result = None
    return result


def get_OBs_from_KPFCC_API(params):
    result = query_KPFCC_API('getKPFObservingBlock', params)
    if result is None:
        return []
    OBs = []
    n = len(result)
    for i,entry in enumerate(result):
        log.debug(f'Parsing entry {i+1} of {n}')
        if not isinstance(entry, dict):
            OBs.append([f'{params}', 'Result is not dict'])
        status = entry.get('status', None)
        OBid = entry.get('id', None)
        if status not in ['OB_FOUND']:
            log.error(f"  ID {OBid}: {entry.get('status', 'No status returned')}")
            OBs.append([OBid, status])
        else:
            # Parse the result as an OB in dict form
            try:
                OB = ObservingBlock(entry)
            except Exception as e:
                log.error(f'Unable to parse entry {i+1} in to an ObservingBlock')
                log.error(entry)
                log.error(f'{e}')
            else:
                if OB.validate():
                    log.debug(f'OB {i+1} is valid')
                    OBs.append(OB)
                else:
                    log.warning(f'OB {i+1} is invalid')
                    if OB.Target is not None:
                        for line in OB.Target.to_lines(comment=True):
                            if line.find('ERR') >= 0:
                                log.warning(line)
                    for obs in OB.Observations:
                        for line in obs.to_lines(comment=True):
                            if line.find('ERR') >= 0:
                                log.warning(line)
    return OBs
