from pathlib import Path
import os
import logging
from datetime import datetime, timedelta
from time import sleep
import subprocess
import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction

from ..fiu.InitializeTipTilt import InitializeTipTilt
from ..fiu.SetTipTiltCalculations import SetTipTiltCalculations
from ..guider.SetGuiderExpTime import SetGuiderExpTime


##-------------------------------------------------------------------------
## Create logger object
##-------------------------------------------------------------------------
this_file_name = Path(__file__).name.replace(".py", "")

log = logging.getLogger(f'{this_file_name}')
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
now_str = utnow.strftime('%Y%m%dat%H%M%S')
date = utnow-timedelta(days=1)
date_str = date.strftime('%Y%b%d').lower()
log_dir = Path(f"/s/sdata1701/{os.getlogin()}/{date_str}/script_logs/")
if log_dir.exists() is False:
    log_dir.mkdir(parents=True)
LogFileName = log_dir / f"{this_file_name}_{now_str}.log"
LogFileHandler = logging.FileHandler(LogFileName)
LogFileHandler.setLevel(logging.DEBUG)
LogFileHandler.setFormatter(LogFormat)
log.addHandler(LogFileHandler)


class TipTiltPerformanceCheck(KPFTranslatorFunction):
    '''Take data to measure tip tilt performance.
    
    fps
    exptime
    
    - Turn CONTINUOUS on
    - Turn TIPTILT on
    - Take image sequence at [fps] for [exptime] with open loop tracking
        - Store cube of images
        - Record OBJECTnRAW values
    - Turn TIPTILT_CONTROL on
    - For a set of gain values:
        - Set TIPTILT_GAIN
        - Take image sequence at [fps] for [exptime]
            - Store cube of images
            - Record OBJECTnRAW values
            - Record DISP2REQ commands
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        kpfguide = ktl.cache('kpfguide')
        duration = args.get('duration', 10)
        log.info("###########")
        if args.get('comment', '') != '': log.info(args.get('comment', ''))
        log.info(f"args = {args}")
        log.info(f"kpfguide.FPS = {kpfguide['FPS'].read()}")
        log.info(f"kpfguide.ITIME = {kpfguide['ITIME'].read()}")
        log.info(f"kpfguide.TIPTILT_GAIN = {kpfguide['TIPTILT_GAIN'].read()}")
        log.info(f"kpfguide.TIPTILT_CONTROL = {kpfguide['TIPTILT_CONTROL'].read()}")
        log.info("###########")

        gshow_file = log_dir / Path(f'{this_file_name}_{now_str}.txt')
        gshow_cmd = ['gshow', '-s', 'kpfguide', 'OBJECT%RAW', '-c',
                     '-timestamp', '-binary']
        log.info(f"Starting: {' '.join(gshow_cmd)}")
        with open(gshow_file, 'w') as FO:
            process = subprocess.Popen(gshow_cmd, shell=False,
                                       stdout=FO, stderr=FO)

        log.info(f"Start data cube collection")
        kpfguide['TRIGGER'].write('Active')
        sleep(duration)
        kpfguide['TRIGGER'].write('Inactive')
        lastcube = kpfguide['LASTTRIGFILE'].read()
        log.info(f"LASTTRIGFILE: {lastcube}")
        log.info('Killing gshow')
        process.kill()

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        from collections import OrderedDict
        args_to_add = OrderedDict()
        args_to_add['duration'] = {'type': float,
                    'help': 'Duration in seconds of each test data set.'}
        args_to_add['comment'] = {'type': str,
                    'help': 'Comment for log'}
        parser = cls._add_args(parser, args_to_add, print_only=False)
        return super().add_cmdline_args(parser, cfg)
