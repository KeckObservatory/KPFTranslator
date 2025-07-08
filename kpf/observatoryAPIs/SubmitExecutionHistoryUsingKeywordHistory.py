import os
import sys
import time
import datetime
import json
import requests
import numpy as np

import ktl
import keygrabber

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.observatoryAPIs.KPFCC import query_KPFCC_API


##-------------------------------------------------------------------------
## SubmitExecutionHistoryUsingKeywordHistory
##-------------------------------------------------------------------------
class SubmitExecutionHistoryUsingKeywordHistory(KPFFunction):
    '''
    '''
    @classmethod
    def pre_condition(cls, args):
        OBid = args.get('OBid', None)
        if OBid is None:
            raise FailedPreCondition('OBid must be provided')

    @classmethod
    def perform(cls, args):
        log.info(f"Running {cls.__name__}")
        OBid = args.get('OBid', '')

        params = {'id': args.get('OBid', '')}

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
            log.error(f'SubmitExecutionHistory: Mismatch in start times and exposure times')
            log.error(f'SubmitExecutionHistory: {len(params["exposure_start_times"])} Exposure Start Times')
            log.error(f'SubmitExecutionHistory: {len(params["exposure_times"])} Exposure Times')
            log.error(f'SubmitExecutionHistory: Readout: {readout}')
            sys.exit(0)
            raise KPFException(f'Mismatch in start times and exposure times')

        log.info('Submitting history to DB:')
        log.info(params)
        result = query_KPFCC_API('addObservingBlockHistory', params=params)
        log.info(f"Response: {result}")

    @classmethod
    def post_condition(cls, args):
        pass

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('OBid', type=str,
                            help='The unique identifier for the OB to retrieve.')
        return super().add_cmdline_args(parser)
