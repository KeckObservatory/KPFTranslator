import sys
import time
import os
import socket
import functools
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timedelta
from pathlib import Path
import re

import ktl

from kpf import log, cfg
from kpf.exceptions import *


##-----------------------------------------------------------------------------
## Tools to generate a custom script log file
##-----------------------------------------------------------------------------
def add_script_handler(this_file_name):
    log = logging.getLogger('KPFTranslator')
    for handler in log.handlers:
        if isinstance(handler, RotatingFileHandler):
            kpflog_filehandler = handler
    ## Set up script log file
    utnow = datetime.utcnow()
    now_str = utnow.strftime('%Y%m%dat%H%M%S')
    date = utnow-timedelta(days=1)
    date_str = date.strftime('%Y%b%d').lower()
    script_log_path = Path(kpflog_filehandler.baseFilename).parent / date_str
    if script_log_path.exists() is False:
        script_log_path.mkdir(mode=0o777, parents=True)
        # Try to set permissions on the date directory
        # necessary because the mode input to mkdir is modified by umask
        try:
            os.chmod(script_log_path, 0o777)
        except OSError as e:
            pass
    script_logfile = script_log_path / f"{now_str}_{this_file_name}.log"
    ScriptLogFileHandler = logging.FileHandler(script_logfile)
    ScriptLogFileHandler.setLevel(logging.DEBUG)
    ScriptLogFileHandler.format = kpflog_filehandler.format
    log.addHandler(ScriptLogFileHandler)
    return log

def remove_script_handler(this_file_name):
    log = logging.getLogger('KPFTranslator')
    script_handler_index = None
    for i,handler in enumerate(log.handlers):
        if isinstance(handler, RotatingFileHandler):
            filename = Path(handler.baseFilename).name
            if re.search(f"{this_file_name}_", filename) is not None:
                ScriptLogFileHandler = handler
                script_handler_index = i
    if script_handler_index is not None:
        log.handlers.pop(script_handler_index)


##-----------------------------------------------------------------------------
## Functions to interact with kpfconfig.SCRIPT% keywords
##-----------------------------------------------------------------------------
def set_script_keywords(scriptname, PID):
    '''Function to write name, PID, and host to kpfconfig.SCRIPT% keywords
    '''
    kpfconfig = ktl.cache('kpfconfig')
    log.debug(f"Registering script {scriptname} with PID {PID}")
    kpfconfig['SCRIPTNAME'].write(scriptname)
    kpfconfig['SCRIPTPID'].write(PID)
    user_at_host = f"{os.getlogin()}@{socket.gethostname()}"
    kpfconfig['SCRIPTHOST'].write(user_at_host)


def clear_script_keywords():
    '''Function to clear kpfconfig.SCRIPT% keywords
    '''
    kpfconfig = ktl.cache('kpfconfig')
    log.debug("Clearing SCRIPTNAME and SCRIPTPID")
    kpfconfig['SCRIPTNAME'].write('None')
    kpfconfig['SCRIPTPID'].write(-1)
    kpfconfig['SCRIPTHOST'].write('')
    kpfconfig['SCRIPTSTOP'].write('No')


def check_script_running():
    '''Function to check if a script is running via kpfconfig.SCRIPT% keywords
    '''
    kpfconfig = ktl.cache('kpfconfig')
    scriptname = kpfconfig['SCRIPTNAME'].read()
    pid = kpfconfig['SCRIPTPID'].read()
    if scriptname not in ['None', '']:
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
        log.warning("SCRIPTSTOP requested. Resetting SCRIPTSTOP and exiting")
        scriptstop.write('No')
        clear_script_keywords()
        raise ScriptStopTriggered("SCRIPTSTOP triggered")


def wait_for_script(newscript='queued script', timeout=1800):
    SCRIPTPID = ktl.cache('kpfconfig', 'SCRIPTPID')
    pid = SCRIPTPID.read(binary=True)
    if pid >= 0:
        SCRIPTNAME = ktl.cache('kpfconfig', 'SCRIPTNAME').read()
        log.info(f'{newscript}: Another script is running: {SCRIPTNAME}(PID {pid})')
        log.info(f'{newscript}: Waiting up to {timeout:.0f}s for it to end')
        success = SCRIPTPID.waitFor("==-1", timeout=timeout)
        if success is False:
            msg = f'{newscript}: Timeout waiting for {SCRIPTNAME} finish.'
            raise KPFException(msg)
        else:
            log.info(f'{newscript}: Script {SCRIPTNAME} no longer running')
            time.sleep(10) # time shim


##-----------------------------------------------------------------------------
## Decorators to interact with kpfconfig.SCRIPT% keywords
##-----------------------------------------------------------------------------
def obey_scriptrun(func):
    @functools.wraps(func)
    def wrapper_decorator(*args, **kwargs):
        check_script_running()
        value = func(*args, **kwargs)
        return value
    return wrapper_decorator


def register_script(scriptname, pid):
    def decorator_register_as_script(func):
        @functools.wraps(func)
        def wrapper_register_as_script(*args, **kwargs):
            set_script_keywords(scriptname, pid)
            value = func(*args, **kwargs)
            clear_script_keywords()
            return value
        return wrapper_register_as_script
    return decorator_register_as_script


##-----------------------------------------------------------------------------
## Decorator to add and remove script log file output
##-----------------------------------------------------------------------------
def add_script_log(this_file_name):
    def decorator_add_scriptlog(func):
        @functools.wraps(func)
        def wrapper_add_scriptlog(*args, **kwargs):
            add_script_handler(this_file_name)
            value = func(*args, **kwargs)
            remove_script_handler(this_file_name)
            return value
        return wrapper_add_scriptlog
    return decorator_add_scriptlog
