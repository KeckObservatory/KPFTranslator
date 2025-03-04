import os
from pathlib import Path
import configparser
import logging
from logging.handlers import RotatingFileHandler
import datetime
from packaging import version
import yaml

from kpf.exceptions import *


##-------------------------------------------------------------------------
## Load configuration values
##-------------------------------------------------------------------------
def load_config(instrument='kpf'):
    config_files = [Path(__file__).parent / f'{instrument}_inst_config.ini']
    config = configparser.ConfigParser(inline_comment_prefixes=(';','#',))
    config.read(config_files)
    return config

cfg = load_config(instrument='kpf')


##-------------------------------------------------------------------------
## Create logger object
##-------------------------------------------------------------------------
def create_KPF_log():
    log = logging.getLogger('KPFTranslator')
    log.setLevel(logging.DEBUG)
    ## Set up console output
    LogConsoleHandler = logging.StreamHandler()
    LogConsoleHandler.setLevel(logging.INFO)
    LogFormat = logging.Formatter('%(asctime)s %(levelname)8s: %(message)s')
    LogConsoleHandler.setFormatter(LogFormat)
    log.addHandler(LogConsoleHandler)
    try:
        ## Set up file output
        logdir = Path(f'/s/sdata1701/KPFTranslator_logs/')
        if logdir.exists() is False:
            logdir.mkdir(mode=0o777, parents=True)
        LogFileName = logdir / 'KPFTranslator.log'
        LogFileHandler = RotatingFileHandler(LogFileName,
                                             maxBytes=100*1024*1024, # 100 MB
                                             backupCount=1000) # Keep old files
        LogFileHandler.setLevel(logging.DEBUG)
        LogFileHandler.setFormatter(LogFormat)
        log.addHandler(LogFileHandler)
        # Try to change permissions in case they are bad
        try:
            os.chmod(LogFileName, 0o666)
        except OSError as e:
            pass
    except:
        pass
    return log


log = create_KPF_log()
