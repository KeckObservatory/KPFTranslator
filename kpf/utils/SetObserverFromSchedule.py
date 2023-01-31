import requests
import json
from datetime import datetime, timedelta

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)
from ..spectrograph.SetObserver import SetObserver


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
        return True

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

        if nKPFprograms == 0:
            log.warning(f"No KPF programs found on schedule")
            progname = None
        elif nKPFprograms == 1:
            progname = KPF_programs[0]['ProjCode']
        elif nKPFprograms > 1:
            print()
            print(f"########################################")
            print(f"  Found {nKPFprograms} KPF programs for tonight:")
            for project_code in project_codes:
                print(f"    {project_code}")
            print(f"  Please entry the program ID for your observations:")
            print(f"########################################")
            print()
            progname = input()
            if progname.strip() not in project_codes:
                log.warning(f"Project code {progname} not on schedule")
                progname = None

        if progname is None:
            log.warning(f"Not setting observers")
        else:
            this_program = [p for p in KPF_programs if p['ProjCode'] == progname]
            log.debug(f"Found {len(this_program)} entries for {progname} in schedule for tonight")
            if len(this_program) > 0:
                observers = this_program[0]['Observers']
                log.info(f"Setting PROGNAME={progname} and observer list based on telescope schedule:")
                log.info(f"{observers}")
                SetProgram.execute({'progname': progname})
                SetObserver.execute({'observer': observers})
            else:
                log.error(f"Failed to set observers. Could not find this program on the schedule.")

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass
