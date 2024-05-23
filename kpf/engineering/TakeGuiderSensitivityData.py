import time
import os
from pathlib import Path
import logging
from datetime import datetime, timedelta
from astropy.table import Table, Row

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.scripts import (register_script, obey_scriptrun, check_scriptstop,
                         add_script_log)
from kpf.guider.SetGuiderGain import SetGuiderGain
from kpf.guider.SetGuiderFPS import SetGuiderFPS


class TakeGuiderSensitivityData(KPFTranslatorFunction):
    '''
    '''
    @classmethod
    @obey_scriptrun
    def pre_condition(cls, OB, logger, cfg):
        check_input(OB, 'Template_Name', allowed_values=['kpf_eng_tgsd'])
        check_input(OB, 'Template_Version', version_check=True, value_min='0.3')
        check_input(OB, 'FPSvalues')

    @classmethod
    @register_script(Path(__file__).name, os.getpid())
    @add_script_log(Path(__file__).name.replace(".py", ""))
    def perform(cls, OB, logger, cfg):
        log.info('-------------------------')
        log.info(f"Running {cls.__name__}")
        for key in OB:
            log.debug(f"  {key}: {OB[key]}")
        log.info('-------------------------')

        images_file = log_dir / Path(f'{this_file_name}_images_{now_str}.txt')
        images = Table(names=('cube file', 'fps'),
                       dtype=('a90',       'f4'))

        kpfguide = ktl.cache('kpfguide')
        log.info(f"Guider gain is {kpfguide['GAIN'].read()}")
        log.info(f"Ensuring TRIGCUBE is Active")
        kpfguide['TRIGCUBE'].write('Active')

        all_loops = kpfguide['ALL_LOOPS'].read(binary=True)

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
            kpfguide['TRIGGER'].write('Inactive', wait=False)
            kpfguide['ALL_LOOPS'].write('Inactive')
            # Wait for cube file to be updated
            ktl.waitFor(f"$kpfguide.LASTTRIGFILE != '{initial_lastfile}'")
            cube_file = kpfguide['LASTTRIGFILE'].read()
            log.info(f"  cube file: {cube_file}")
            if all_loops == 1:
                kpfguide['ALL_LOOPS'].write(1)
            row = {'cube file': cube_file,
                   'fps': FPS}
            images.add_row(row)
            if images_file.exists():
                images_file.unlink()
            images.write(images_file, format='ascii.csv')

    @classmethod
    def post_condition(cls, OB, logger, cfg):
        pass
