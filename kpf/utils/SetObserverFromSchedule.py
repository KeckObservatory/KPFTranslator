import time
from datetime import datetime, timedelta

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.utils.telsched import get_schedule
from kpf.spectrograph.SetObserver import SetObserver
from kpf.spectrograph.SetProgram import SetProgram


##-----------------------------------------------------------------------------
## SetObserverFromSchedule
##-----------------------------------------------------------------------------
class SetObserverFromSchedule(KPFTranslatorFunction):
    '''
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def perform(cls, args, logger, cfg):
        utnow = datetime.utcnow()
        date = utnow-timedelta(days=1)
        date_str = date.strftime('%Y-%m-%d')
        KPF_programs = [s for s in get_schedule(date_str, 1)
                        if s['Instrument'] == 'KPF']
        nKPFprograms = len(KPF_programs)
        log.debug(f"Found {nKPFprograms} KPF programs in schedule for tonight")
        project_codes = [p['ProjCode'] for p in KPF_programs]

        # Look at the schedule to find programs scheduled for tonight
        if nKPFprograms == 0:
            log.warning(f"No KPF programs found on schedule")
            progname = None
        elif nKPFprograms == 1:
            progname = KPF_programs[0]['ProjCode']
        elif nKPFprograms > 1:
            progname = args.get('progname', None)
            if progname is None:
                print()
                print(f"########################################")
                print(f"  Found {nKPFprograms} KPF programs for tonight:")
                for project_code in project_codes:
                    print(f"    {project_code}")
                print(f"  Please enter the program ID for your observations:")
                print(f"########################################")
                print()
                progname = input()
                if progname.strip() not in project_codes:
                    log.warning(f"Project code {progname} not on schedule")

        # Set the program
        if progname is None:
            time.sleep(0.5) # try time shim for log line
            print()
            print(f"  Please enter the program ID for your observations:")
            print()
            progname = input()
        if progname == '':
            log.info('No progname specified')
        else:
            SetProgram.execute({'progname': progname})

        # Set Observers
        this_program = [p for p in KPF_programs if p['ProjCode'] == progname]
        if len(this_program) > 0:
            observers = this_program[0]['Observers']
        else:
            print()
            print(f"  Please enter the observer names:")
            print()
            observers = input()
        log.info(f"Setting observer list: {observers}")
        SetObserver.execute({'observer': observers})

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass
