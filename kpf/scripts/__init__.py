import sys
import os
import requests
import json
import socket

import ktl

from .. import log, KPFException, FailedPreCondition


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


# def add_script_registry(func):
#     '''Decorator to add register_script and clear_script
#     '''
#     import functools
#     @functools.wraps(func)
#     def wrapper_decorator(*args, **kwargs):
#         pid = os.getpid()
#         log.debug(f'Decorator is registering script: {func.__file__}, {pid}')
#         register_script(func.__file__, pid)
#         value = func(*args, **kwargs)
#         clear_script()
#         return value
#     return wrapper_decorator
#
#
# from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
#
# class KPFSscript(KPFTranslatorFunction):
#     def execute(cls, args, logger=None, cfg=None)
#         register_script(Path(__file__).name, os.getpid())
#         print(args)
#         print(logger)
#         print(cfg)
#         super().execute(args, logger=logger, cfg=cfg)
#         clear_script()


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
