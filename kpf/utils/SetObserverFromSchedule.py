import time
import requests
import json
from datetime import datetime, timedelta

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.spectrograph.SetObserver import SetObserver
from kpf.spectrograph.SetProgram import SetProgram


##-----------------------------------------------------------------------------
## Functions to interact with telescope DB
##-----------------------------------------------------------------------------
def querydb(req):
    '''A simple wrapper to form a generic API level query to the telescope
    schedule web API.  Returns a JSON object with the result of the query.
    '''
    url = f"https://www.keck.hawaii.edu/software/db_api/telSchedule.php?{req}"
    r = requests.get(url)
    return json.loads(r.text)


def get_schedule(date, tel):
    '''Use the querydb function and getSchedule of the telescope schedule web
    API with arguments for date and telescope number.  Returns a JSON object
    with the schedule result.
    '''
    if tel not in [1,2]:
        raise KPFError(f"Telescope number in query must be 1 or 2")
    req = f"cmd=getSchedule&date={date}&telnr={tel}"
    result = querydb(req)
    return result


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
