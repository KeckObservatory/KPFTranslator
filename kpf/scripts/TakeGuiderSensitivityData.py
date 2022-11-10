from pathlib import Path
import logging
from datetime import datetime, timedelta

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)
from ..guider.SetGuiderGain import SetGuiderGain
from ..guider.SetGuiderFPS import SetGuiderFPS


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


class TakeGuiderSensitivityData(KPFTranslatorFunction):
    '''
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
#         check_input(args, 'FPS')
#         check_input(args, 'gains')
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        kpfguide = ktl.cache('kpfguide')
        exptime = args.get('exptime', 10)
        FPSvalues = [10, 20]
        gains = ['low']

        images_file = log_dir / Path(f'{this_file_name}_images_{now_str}.txt')
        images = Table(names=('stacked file', 'cube file', 'gain', 'fps', 'exptime'),
                       dtype=('a90',          'a90',       'a10',   'f4', 'f4'))


        for FPS in FPSvalues:
            for gain in gains:
                log.info(f"Setting gain to {gain} and FPS to {FPS}")
                SetGuiderGain.execute({'gain': gain})
                SetGuiderFPS.execute({'fps': FPS})
                # Wait for the stacked file to increment
                initial_lastfile = kpfguide['LASTFILE'].read()
                initial_lasttrigfile = kpfguide['LASTTRIGFILE'].read()
                ktl.waitFor(f"$kpfguide.LASTFILE != '{initial_lastfile}'")
                # Start cube collection simultaneous with stacked file
                kpfguide['TRIGGER'].write(1)
                # End cube collection simultaneous with stacked file being written
                initial_lastfile = kpfguide['LASTFILE'].read()
                ktl.waitFor(f"$kpfguide.LASTFILE != '{initial_lastfile}'")
                kpfguide['TRIGGER'].write(0)
                # Wait for cuber file to be updated
                ktl.waitFor(f"$kpfguide.LASTTRIGFILE != '{initial_lasttrigfile}'")
                stacked_file = kpfguide['LASTFILE'].read()
                log.info(f"  stacked file: {stacked_file}")
                cube_file = kpfguide['LASTTRIGFILE'].read()
                log.info(f"  cube file: {cube_file}")
                row = {'stacked file': stacked_file,
                       'sube file': cube_file,
                       'gain': gain,
                       'fps': FPS, 'exptime': exptime}
                images.add_row(row)


    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True

#     @classmethod
#     def add_cmdline_args(cls, parser, cfg=None):
#         '''The arguments to add to the command line interface.
#         '''
#         from collections import OrderedDict
#         args_to_add = OrderedDict()
#         args_to_add['OBfile'] = {'type': str,
#                                  'help': ('A YAML fortmatted file with the OB '
#                                           'to be executed. Will override OB '
#                                           'data delivered as args.')}
#         parser = cls._add_args(parser, args_to_add, print_only=False)
#         return super().add_cmdline_args(parser, cfg)
