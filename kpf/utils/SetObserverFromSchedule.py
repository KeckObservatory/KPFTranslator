import time
from datetime import datetime, timedelta

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.utils.telsched import get_schedule, get_ToO_programs
from kpf.spectrograph.SetObserver import SetObserver
from kpf.spectrograph.SetProgram import SetProgram


##-----------------------------------------------------------------------------
## SetObserverFromSchedule
##-----------------------------------------------------------------------------
class SetObserverFromSchedule(KPFTranslatorFunction):
    '''Look up the telescope schedule and try to determine the observer names
    based on the current date and the scheduled programs.

    If only one KPF program is on the schedule, the script will use that to set
    the observer names.  If multiple programs are on the schedule, it will use
    the progname input (see below) or query the user if no progname is given.

    ARGS:
    =====
    :progname: `str` The program name to set if a choice is needed.
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
                        if s['Instrument'] in ['KPF', 'KPF-CC']]
        nKPFprograms = len(KPF_programs)
        log.debug(f"Found {nKPFprograms} KPF programs in schedule for tonight")
        project_codes = [p['ProjCode'] for p in KPF_programs]
        ToO_project_codes, ToO_PIs = get_ToO_programs()

        print()
        print(f"########################################")
        print(f"  Found {nKPFprograms} KPF programs scheduled for tonight:")
        for project_code in project_codes:
            print(f"    {project_code}")
        print(f"  Found {len(ToO_project_codes)} ToO programs:")
        for i,project_code in enumerate(ToO_project_codes):
            print(f"    {project_code} (PI {ToO_PIs[i]})")
        print(f"  Please enter the program ID for your observations:")
        print(f"########################################")
        print()
        progname = input()
        if progname.strip() not in project_codes+ToO_project_codes:
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
