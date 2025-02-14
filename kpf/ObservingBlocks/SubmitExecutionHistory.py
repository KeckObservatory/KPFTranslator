import os
import sys
import time
import datetime
import json
import requests
import numpy as np

import ktl
import keygrabber

from kpf import log, cfg, check_input
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


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
## SubmitExecutionHistory
##-------------------------------------------------------------------------
class SubmitExecutionHistory(KPFFunction):
    '''
    '''
    @classmethod
    def pre_condition(cls, args):
        url = cfg.get('Database', 'url', fallback=None)
        if url is None:
            raise FailedPreCondition('Database URL is not defined in configuration')
        OBid = args.get('OBid', None)
        if OBid is None:
            raise FailedPreCondition('OBid must be provided')

    @classmethod
    def perform(cls, args):
        log.info(f"Running {cls.__name__}")
        url = cfg.get('Database', 'url')
        OBid = args.get('OBid', '')
        apihash = os.getenv('APIHASH', default='')

        params = {}
        SCRIPTPID_hist = keygrabber.retrieve({'kpfconfig': ['SCRIPTPID']},
            begin=time.mktime(datetime.datetime.now().timetuple()))
        log.debug('Getting start time of script')
        begin = SCRIPTPID_hist[0]['time']

        log.debug('Getting OBSERVER history')
        observer_hist = keygrabber.retrieve({'kpfexpose': ['OBSERVER']}, begin=begin)
        params["observer"] = observer_hist[0]['ascvalue']

        log.debug('Getting STARTTIME history')
        start_times = []
        start_hist = keygrabber.retrieve({'kpfexpose': ['STARTTIME']}, begin=begin)
        start_hist.pop(0)
        tzconversion = datetime.timedelta(hours=10)
        for s in start_hist:
            d = datetime.datetime.fromtimestamp(s['time'])
            ut = d + tzconversion
            rounded_ut = round_microseconds(ut)
            start_times.append(truncate_isoformat(rounded_ut))
        params["exposure_start_times"] = start_times

        log.debug('Getting ELAPSED history')
        elapsed_hist = keygrabber.retrieve({'kpfexpose': ['ELAPSED', 'EXPOSE']}, begin=begin)
        exp_times = []
        became_ready = False
        readout = False
        last_elapsed = 0
        for s in elapsed_hist:
            if (s['keyword'] == 'EXPOSE') and (s['ascvalue'] == 'Ready'):
                became_ready = True
#                 print('Became ready')
            elif (s['keyword'] == 'EXPOSE') and (s['ascvalue'] == 'Readout') and became_ready:
                readout = True
#                 print('readout is true')
#                 print(f'Grabbing elapsed: {last_elapsed}')
                exp_times.append(last_elapsed)
            elif (s['keyword'] == 'EXPOSE') and (s['ascvalue'] != 'Readout'):
                readout = False
#                 print('readout is false')
            if (s['keyword'] == 'ELAPSED'):
                last_elapsed = float(s["binvalue"])
        params["exposure_times"] = exp_times

        if len(params["exposure_times"]) != len(params["exposure_start_times"]):
            print(f'Mismatch in start times and exposure times')
            print(f'{len(params["exposure_start_times"])} Exposure Start Times')
            print(f'{len(params["exposure_times"])} Exposure Times')
            print(f'Readout: {readout}')
            sys.exit(0)
            raise KPFException(f'Mismatch in start times and exposure times')

#         log.debug('Getting OBSERVERCOMMENT history')
#         comment_hist = keygrabber.retrieve({'kpfconfig': ['OBSERVERCOMMENT']}, begin=begin)
#         comments = []
#         for s in comment_hist:
#             comments.append(s['ascvalue'])

        # For testing
        comments = ['an observer comment', 'another comment', 'this is a lot of comments for a single OB!',
                    'This is a long soliloquy on the observing conditions during this observation which is here to make sure we do not have overly restrictive string length limits somewhere in the system.',
                    "For completeness, a check on various inconvienient characters:\nJohn O'Meara, Cecilia Payne-Gaposchkin, are question marks ok? (should I even ask?) [perhaps not] {right?}"]
        params["comment"] = '\n'.join(comments)

        # Upload via API
        params["id"] = f"{OBid}"
        print(f'OBid:            {params["id"]}')
        print(f'Observer:        {params["observer"]}')
        print(f'ObserverComment: {params["comment"]}')
        print(f'Start Times:     {params["exposure_start_times"]}')
        print(f'Exposure Times:  {params["exposure_times"]}')
        if OBid in [None, '', ' ', '0', 0]:
            return
        else:
            print('Submitting data to DB:')
            data = requests.post(f"{url}addObservingBlockHistory",
                                 params=params, verify=False)
            print(f"Response: {data}")


    @classmethod
    def post_condition(cls, args):
        pass

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('OBid', type=str,
                            help='The unique identifier for the OB to retrieve.')
        return super().add_cmdline_args(parser)
