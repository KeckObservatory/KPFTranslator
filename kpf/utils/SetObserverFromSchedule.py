import time
from datetime import datetime, timedelta

import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.spectrograph.SetObserver import SetObserver
from kpf.spectrograph.SetProgram import SetProgram
from kpf.observatoryAPIs.GetScheduledPrograms import GetScheduledPrograms

##-----------------------------------------------------------------------------
## SetObserverFromSchedule
##-----------------------------------------------------------------------------
class SetObserverFromSchedule(KPFFunction):
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
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        classical, cadence = GetScheduledPrograms.execute({'semester': 'current'})
        KPF_programs = classical + cadence
        nKPFprograms = len(KPF_programs)
        project_codes = [p['ProjCode'] for p in KPF_programs]

        print()
        print(f"########################################")
        print(f"  Found {nKPFprograms} KPF programs scheduled for tonight:")
        for project_code in project_codes:
            print(f"    {project_code}")
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
    def post_condition(cls, args):
        pass
