import sys
import os
import requests
import json
import socket
import functools

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import log, KPFException, FailedPreCondition

##-----------------------------------------------------------------------------
## Functions to interact with kpfconfig.SCRIPT% keywords
##-----------------------------------------------------------------------------
def register_script(scriptname, PID):
    '''Function to write name, PID, and host to kpfconfig.SCRIPT% keywords
    '''
    kpfconfig = ktl.cache('kpfconfig')
    log.debug(f"Registering script {scriptname} with PID {PID}")
    kpfconfig['SCRIPTNAME'].write(scriptname)
    kpfconfig['SCRIPTPID'].write(PID)
    kpfconfig['SCRIPTHOST'].write(socket.gethostname())


def clear_script():
    '''Function to clear kpfconfig.SCRIPT% keywords
    '''
    kpfconfig = ktl.cache('kpfconfig')
    log.debug("Clearing SCRIPTNAME and SCRIPTPID")
    kpfconfig['SCRIPTNAME'].write('')
    kpfconfig['SCRIPTPID'].write(-1)
    kpfconfig['SCRIPTHOST'].write('')


def check_script_running():
    '''Function to check if a script is running via kpfconfig.SCRIPT% keywords
    '''
    kpfconfig = ktl.cache('kpfconfig')
    scriptname = kpfconfig['SCRIPTNAME'].read()
    pid = kpfconfig['SCRIPTPID'].read()
    if scriptname != '':
        msg = (f"Existing script {scriptname} ({pid}) is running.\n"
               f"If the offending script is not running (PID not listed in ps)\n"
               f"then the script keywords can be cleared by running:\n"
               f"  reset_script_keywords\n"
               f"or invoking it from the FVWM background menu:\n"
               f"  KPF Trouble Recovery --> Reset script keywords")
        raise FailedPreCondition(msg)


def check_script_stop():
    '''Function to check if a stop has been requested via kpfconfig.SCRIPTSTOP
    '''
    scriptstop = ktl.cache('kpfconfig', 'SCRIPTSTOP')
    if scriptstop.read() == 'Yes':
        log.warning("SCRIPTSTOP requested.  Resetting SCRIPTSTOP and exiting")
        scriptstop.write('No')
        clear_script()
        raise KPFException("SCRIPTSTOP triggered")


##-----------------------------------------------------------------------------
## Decorators to interact with kpfconfig.SCRIPT% keywords
##-----------------------------------------------------------------------------
def check_scriptrun(func):
    @functools.wraps(func)
    def wrapper_decorator(*args, **kwargs):
        check_script_running()
        value = func(*args, **kwargs)
        return value
    return wrapper_decorator


def register_as_script(scriptname, pid):
    def decorator_register_as_script(func):
        @functools.wraps(func)
        def wrapper_register_as_script(*args, **kwargs):
            register_script(scriptname, pid)
            value = func(*args, **kwargs)
            clear_script()
            return value
        return wrapper_register_as_script
    return decorator_register_as_script


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
