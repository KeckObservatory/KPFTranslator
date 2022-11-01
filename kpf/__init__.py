import os
from pathlib import Path
import logging
from datetime import datetime, timedelta


##-------------------------------------------------------------------------
## Create logger object
##-------------------------------------------------------------------------
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
