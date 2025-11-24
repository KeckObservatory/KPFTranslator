import sys
import datetime

import ktl
import keygrabber

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


def count_exposures(exp_history):
    expose = [x for x in exp_history if x['keyword'].upper() == 'EXPOSE']
    nexp = 0
    inprogress = False
    for event in expose:
        if event.get('ascvalue') == 'InProgress':
            if inprogress == False:
                nexp +=1
            inprogress = True
        else:
            inprogress = False
    return nexp


class ListLFCRuns(KPFFunction):
    '''

    Args:
        ? (str): 

    KTL Keywords Used:

    - ``
    '''
    @classmethod
    def perform(cls, args):
        ndays = args.get('ndays', 1)
        now = datetime.datetime.now()
        if args.get('date', '') in ['', 'now']:
            start = now - datetime.timedelta(days=ndays)
        else:
            start = datetime.datetime.strptime(args.get('date'), '%Y-%m-%d') - datetime.timedelta(days=ndays)
        LFC_history = keygrabber.retrieve({'kpfcal': ['OPERATIONMODE']},
                                          begin=start.timestamp(),
                                          end=now.timestamp())
        astrocomb = [x for x in LFC_history if x['ascvalue'] == 'AstroComb']

#         kws = {'kpfcal': ['OPERATIONMODE', 'POS_INTENSITY', 'SPECFLATIR',
#                           'SPECFLATVIS', 'VISFLUX', 'WOBBLE'],
#                'kpfexpose': ['EXPOSE', 'OBJECT', 'FRAMENO']}
        kws = {'kpfexpose': ['EXPOSE', 'OBJECT', 'FRAMENO']}
        for event in astrocomb:
            event_time = datetime.datetime.fromtimestamp(event.get('time')).strftime('%Y-%m-%d %H:%M:%S.%f')
            later_astrocomb = [x for x in LFC_history if x.get('time') > event.get('time')]
            end = event.get('time')
            for later in later_astrocomb:
                if later.get('ascvalue') != 'AstroComb':
                    end = later.get('time')
                    break
            exp_history = keygrabber.retrieve(kws,
                                              begin=event.get('time'),
                                              end=end)
            exp_history = [x for x in exp_history if x.get('time') > event.get('time')]
            duration = end-event.get('time')
            print(f"{event_time}: {event.get('ascvalue'):9s} {later.get('ascvalue'):11s} {duration:<6.1f}s {count_exposures(exp_history)}")


    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('ndays', type=int,
                            help='Number of days) to examine')
        parser.add_argument('date', type=str, default='',
                            help='Starting date (HST) to examine')
        return super().add_cmdline_args(parser)

