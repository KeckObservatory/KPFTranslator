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
def _register_script(scriptname, PID):
    '''Function to write name, PID, and host to kpfconfig.SCRIPT% keywords
    '''
    kpfconfig = ktl.cache('kpfconfig')
    log.debug(f"Registering script {scriptname} with PID {PID}")
    kpfconfig['SCRIPTNAME'].write(scriptname)
    kpfconfig['SCRIPTPID'].write(PID)
    kpfconfig['SCRIPTHOST'].write(socket.gethostname())


def _clear_script():
    '''Function to clear kpfconfig.SCRIPT% keywords
    '''
    kpfconfig = ktl.cache('kpfconfig')
    log.debug("Clearing SCRIPTNAME and SCRIPTPID")
    kpfconfig['SCRIPTNAME'].write('')
    kpfconfig['SCRIPTPID'].write(-1)
    kpfconfig['SCRIPTHOST'].write('')


def _check_script_running():
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


def check_scriptstop():
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
def obey_scriptrun(func):
    @functools.wraps(func)
    def wrapper_decorator(*args, **kwargs):
        _check_script_running()
        value = func(*args, **kwargs)
        return value
    return wrapper_decorator


def register_script(scriptname, pid):
    def decorator_register_as_script(func):
        @functools.wraps(func)
        def wrapper_register_as_script(*args, **kwargs):
            _register_script(scriptname, pid)
            value = func(*args, **kwargs)
            _clear_script()
            return value
        return wrapper_register_as_script
    return decorator_register_as_script


def verify_cleared(func):
    @functools.wraps(func)
    def wrapper_decorator(*args, **kwargs):
        # Check if script is cleared
        kpfconfig = ktl.cache('kpfconfig')
        if kpfconfig['SCRIPTNAME'].read() != '':
            log.warning("Clearing SCRIPTNAME")
            kpfconfig['SCRIPTNAME'].write('')
        if kpfconfig['SCRIPTPID'].read(binary=True) != -1:
            log.warning("Clearing SCRIPTPID")
            kpfconfig['SCRIPTPID'].write(-1)
        if kpfconfig['SCRIPTHOST'].read() != '':
            log.warning("Clearing SCRIPTHOST")
            kpfconfig['SCRIPTHOST'].write('')
        value = func(*args, **kwargs)
        return value
    return wrapper_decorator
