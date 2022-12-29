import time
import os
from pathlib import Path
import logging
from datetime import datetime, timedelta
from astropy.table import Table, Row

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)
from . import register_as_script, check_scriptrun, check_script_stop
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
    @check_scriptrun
    def pre_condition(cls, OB, logger, cfg):
        check_input(OB, 'Template_Name', allowed_values=['kpf_eng_tgsd'])
        check_input(OB, 'Template_Version', version_check=True, value_min='0.3')
        check_input(OB, 'GuideCamGain', allowed_values=['high', 'medium', 'low'])
        check_input(OB, 'FPSvalues')
        return True

    @classmethod
    @register_as_script(Path(__file__).name, os.getpid())
    def perform(cls, OB, logger, cfg):
        log.info('-------------------------')
        log.info(f"Running TakeGuiderSensitivityData OB")
        for key in OB:
            log.debug(f"  {key}: {OB[key]}")
        log.info('-------------------------')

        images_file = log_dir / Path(f'{this_file_name}_images_{now_str}.txt')
        images = Table(names=('cube file', 'gain', 'fps'),
                       dtype=('a90',       'a10',  'f4'))

        kpfguide = ktl.cache('kpfguide')

        gain = OB.get('GuideCamGain')
        log.info(f"Setting gain to {gain}")
        SetGuiderGain.execute(OB)

        cube_duration = OB.get('cube_duration')
        for FPS in OB.get('FPSvalues'):
            log.info(f"Setting FPS to {FPS}")
            SetGuiderFPS.execute({'GuideFPS': FPS})

            # Start cube collection 
            log.info(f'Starting data collection for {cube_duration} s')
            initial_lastfile = kpfguide['LASTTRIGFILE'].read()
            kpfguide['TRIGGER'].write('Active')
            log.debug(f"Sleeping {cube_duration} s")
            time.sleep(cube_duration)
            # End cube collection
            kpfguide['TRIGGER'].write('Inactive')
            # Wait for cuber file to be updated
            ktl.waitFor(f"$kpfguide.LASTTRIGFILE != '{initial_lastfile}'")
            cube_file = kpfguide['LASTTRIGFILE'].read()
            log.info(f"  cube file: {cube_file}")
            row = {'cube file': cube_file,
                   'gain': gain,
                   'fps': FPS}
            images.add_row(row)
            if images_file.exists():
                images_file.unlink()
            images.write(images_file, format='ascii.csv')

    @classmethod
    def post_condition(cls, OB, logger, cfg):
        return True
