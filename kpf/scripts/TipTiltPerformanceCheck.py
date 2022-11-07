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
        log.info("###########")

#         gains = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]
        gains = [0.1, 0.3, 0.5]

        log.info('Initializing tip tilt mirror')
        InitializeTipTilt.execute({})
        log.info('Setting CONTINUOUS to active')
        kpfguide['CONTINUOUS'].write('Active')
        log.info('Setting TIPTILT calculations to active')
        SetTipTiltCalculations.execute({'calculations': 'Active'})

        gshow_file = log_dir / Path(f'{this_file_name}_{now_str}.txt')
        gshow_cmd = ['gshow', '-s', 'kpfguide', 'OBJECT%RAW', '-c',
                     '-timestamp', '-binary', '>', f"{gshow_file}"]
        log.info(f"Starting: {' '.join(gshow_cmd)}")
        process = subprocess.Popen(' '.join(gshow_cmd), shell=True,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)

        log.info(f"Take data with open loop tracking")
        kpfguide['TRIGGER'].write('Active')
        sleep(duration)
        kpfguide['TRIGGER'].write('Inactive')
        lastcube = kpfguide['LASTTRIGFILE'].read()
        log.info(f"LASTTRIGFILE Open Loop: {lastcube}")

        kpfguide['TIPTILT_CONTROL'].write('Active')

        for i,gain in enumerate(gains):
            kpfguide['TIPTILT_GAIN'].write(gain)
            log.info(f"Waiting for TIPTILT_PHASE to be Tracking")
            ktl.waitFor('($kpfguide.TIPTILT_PHASE == Tracking)', timeout=5)
            log.info('Sleeping for 2 seconds')
            sleep(2)
            log.info(f"Take data with tip tilt active, gain={gain:.1f}")
            kpfguide['TRIGGER'].write('Active')
            sleep(duration)
            kpfguide['TRIGGER'].write('Inactive')
            lastcube = kpfguide['LASTTRIGFILE'].read()
            log.info(f"LASTTRIGFILE gain={gain:.1f}: {lastcube}")

        log.info('Killing gshow')
        process.kill()

        log.info('Setting TIPTILT_CONTROL to inactive')
        kpfguide['TIPTILT_CONTROL'].write('Inactive')
        log.info('Setting TIPTILT to inactive')
        kpfguide['TIPTILT'].write('Inactive')
        log.info('Setting CONTINUOUS to inactive')
        kpfguide['CONTINUOUS'].write('Inactive')


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
