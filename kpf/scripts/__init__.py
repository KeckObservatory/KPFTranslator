import sys
import requests
import json

import ktl

from .. import log, FailedPreCondition


def register_script(scriptname, PID):
    kpfconfig = ktl.cache('kpfconfig')
    log.debug(f"Registering script {scriptname} with PID {PID}")
    kpfconfig['SCRIPTNAME'].write(scriptname)
    kpfconfig['SCRIPTPID'].write(PID)


def clear_script():
    kpfconfig = ktl.cache('kpfconfig')
    log.debug("Clearing SCRIPTNAME and SCRIPTPID")
    kpfconfig['SCRIPTNAME'].write('')
    kpfconfig['SCRIPTPID'].write(-1)


def check_script_running():
    kpfconfig = ktl.cache('kpfconfig')
    scriptname = kpfconfig['SCRIPTNAME'].read()
    pid = kpfconfig['SCRIPTPID'].read()
    if scriptname != '':
        raise FailedPreCondition(f"Existing script {scriptname} ({pid}) is running.")


def check_script_stop():
    scriptstop = ktl.cache('kpfconfig', 'SCRIPTSTOP')
    if scriptstop.read() == 'Yes':
        log.warning("SCRIPTSTOP requested.  Resetting SCRIPTSTOP and exiting")
        scriptstop.write('No')
        clear_script()
        sys.exit(0)


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
