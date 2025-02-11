import time
import datetime
import json
import requests

import ktl
import keygrabber

from kpf import log, cfg, check_input
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


##-------------------------------------------------------------------------
## CheckDewarWeights
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
        params["id"] = f"{OBid}"
        if OBid is None:
            return
        log.info(f"Running {cls.__name__}")
        SCRIPTPID_hist = keygrabber.retrieve({'kpfconfig': ['SCRIPTPID']},
            begin=time.mktime(datetime.datetime.now().timetuple()))
        log.debug('Getting start time of script')
        begin = datetime.datetime.fromtimestamp(SCRIPTPID_history[0]['time'])

        log.debug('Getting OBSERVER history')
        observer_hist = keygrabber.retrieve({'kpfexpose': ['OBSERVER']}, begin=begin)
        params["observer"] = observer_hist[0]['ascvalue']

        log.debug('Getting STARTTIME history')
        start_times = []
        start_hist = keygrabber.retrieve({'kpfexpose': ['STARTTIME']}, begin=begin)
        tzconversion = datetime.timedelta(hours=10)
        for s in start_hist:
            d = datetime.datetime.fromtimestamp(s['time'])
            ut = d + tzconversion
            start_times.append(ut.isoformat())
        params["exposure_start_times"] = start_times

        log.debug('Getting ELAPSED history')
        elapsed_hist = keygrabber.retrieve({'kpfexpose': ['ELAPSED']}, begin=begin)
#         exp_times = []
#         for s in elapsed_hist:
#             d = datetime.datetime.fromtimestamp(s['time'])
#             ut = d + tzconversion
#             exp_times.append(ut.isoformat())
#         params["exposure_times"] = exp_times

#         log.debug('Getting OBSERVERCOMMENT history')
#         comment_hist = keygrabber.retrieve({'kpfconfig': ['OBSERVERCOMMENT']}, begin=begin)
#         comments = []
#         for s in start_hist:
#             d = datetime.datetime.fromtimestamp(s['time'])
#             ut = d + tzconversion
#             start_times.append(ut.isoformat())
#         params["comment"] = '\n'.join(comments)

        # Upload via API
        print(params)
#         url = "https://vm-appserver.keck.hawaii.edu/api/proposalsTest/addObservingBlockHistory"
#         data = requests.post(url, params=params, verify=False)


    @classmethod
    def post_condition(cls, args):
        pass
