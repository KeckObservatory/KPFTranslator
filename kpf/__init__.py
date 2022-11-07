import os
from pathlib import Path
import logging
from datetime import datetime, timedelta


##-------------------------------------------------------------------------
## Create logger object
##-------------------------------------------------------------------------
def create_KPF_log():
    log = logging.getLogger('KPFTranslator')
    log.setLevel(logging.DEBUG)
    ## Set up console output
    LogConsoleHandler = logging.StreamHandler()
    LogConsoleHandler.setLevel(logging.INFO)
    LogFormat = logging.Formatter('%(asctime)s %(levelname)8s: %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')
    LogConsoleHandler.setFormatter(LogFormat)
    log.addHandler(LogConsoleHandler)
    ## Set up file output
    utnow = datetime.utcnow()
    date = utnow-timedelta(days=1)
    date_str = date.strftime('%Y%b%d').lower()
    logdir = Path(f"/s/sdata1701/{os.getlogin()}/{date_str}/logs")
    if logdir.exists() is False:
        logdir.mkdir(parents=True)
    LogFileName = logdir / 'KPFTranslator.log'
    LogFileHandler = logging.FileHandler(LogFileName)
    LogFileHandler.setLevel(logging.DEBUG)
    LogFileHandler.setFormatter(LogFormat)
    log.addHandler(LogFileHandler)
    return log

log = create_KPF_log()


##-------------------------------------------------------------------------
## Define some exceptions
##-------------------------------------------------------------------------
class KPFException(Exception):
    def __init__(self, message=""):
        self.message = message
        log.error(self.message)
        super().__init__(self.message)


class FailedPreCondition(KPFException):
    def __init__(self, pcmessage=""):
        self.pcmessage = f"Failed PreCondition: {pcmessage}"
        super().__init__(self.pcmessage)


class FailedPostCondition(KPFException):
    def __init__(self, pcmessage=""):
        self.pcmessage = f"Failed PostCondition: {pcmessage}"
        super().__init__(self.pcmessage)


class FailedToReachDestination(FailedPostCondition):
    def __init__(self, destination="", value=""):
        self.destination = destination
        self.value = value
        msg = f"{value} != {destination}"
        super().__init__(msg)


##-------------------------------------------------------------------------
## Utility functions
##-------------------------------------------------------------------------
def check_input(args, input_name, allowed_values=None,
                value_min=None, value_max=None):
        target = args.get(input_name, None)
        if target is None:
            raise FailedPreCondition(f"Input {input_name} is None")
        if value_min is not None:
            if target < value_min:
                raise FailedPreCondition(f"Input {input_name} value {target} "
                                         f"below minimum allowed ({value_min})")
        if value_max is not None:
            if target > value_max:
                raise FailedPreCondition(f"Input {input_name} value {target} "
                                         f"above maximum allowed ({value_max})")
        if allowed_values is not None:
            if target not in allowed_values:
                raise FailedPreCondition(f"Input {input_name} value {target} "
                                         f"not in allowed values")
