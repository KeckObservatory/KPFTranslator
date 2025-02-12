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
    '''Round the given date time object to 2 microseconds.
    '''
    factor = 10**(6-ndecimals)
    rounded = ut.replace(microsecond=int(np.round(ut.microsecond/factor)*factor))
    return rounded


##-------------------------------------------------------------------------
## CollectExecutionHistory
##-------------------------------------------------------------------------
class CollectExecutionHistory(KPFFunction):
    '''
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        OBid = args.get('OBid', None)
        params = {}
        log.info(f"Running {cls.__name__}")
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
            start_times.append(rounded_ut.isoformat()[:-4])
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
        comments = []
#         for s in comment_hist:
#             comments.append(s['ascvalue'])
        params["comment"] = '\n'.join(comments)

        # Upload via API
        params["id"] = f"{OBid}"
        print(f'OBid:            {params["id"]}')
        print(f'Observer:        {params["observer"]}')
        print(f'ObserverComment: {params["comment"]}')
        print(f'Start Times:     {params["exposure_start_times"]}')
        print(f'Exposure Times:  {params["exposure_times"]}')
        if OBid is None:
            return
        else:
            url = "https://vm-appserver.keck.hawaii.edu/api/proposalsTest/addObservingBlockHistory"
            data = requests.post(url, params=params, verify=False)


    @classmethod
    def post_condition(cls, args):
        pass
