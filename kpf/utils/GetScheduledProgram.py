import time
from datetime import datetime, timedelta

import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.utils.telsched import get_schedule
from kpf.spectrograph.SetProgram import SetProgram


##-----------------------------------------------------------------------------
## SetObserverFromSchedule
##-----------------------------------------------------------------------------
class GetScheduledProgram(KPFFunction):
    '''Look up the telescope schedule and try to determine the program ID
    based on the current date and the scheduled programs.
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        utnow = datetime.utcnow()
        utnow_decimal = utnow.hour + utnow.minute/60
        date = utnow-timedelta(days=1)
        date_str = date.strftime('%Y-%m-%d')
        KPF_programs = get_schedule(date_str)
        for progam in KPF_programs:
            start_time_h, start_time_m = program['StartTime'].split(':')
            start_time = int(start_time_h) + int(start_time_m)/60
            end_time_h, end_time_m = program['EndTime'].split(':')
            end_time = int(end_time_h) + int(end_time_m)/60
            if utnow_decimal >= start_time and utnow_decimal < end_time:
                return progam['ProjCode']
        log.warning('Unable to determine program ID from schedule, using ENG')
        return 'ENG'

    @classmethod
    def post_condition(cls, args):
        pass
