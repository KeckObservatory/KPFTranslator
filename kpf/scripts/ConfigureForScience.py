import os
import time
from packaging import version
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.scripts import (register_script, obey_scriptrun, check_scriptstop,
                         add_script_log)
from kpf.calbench.CalLampPower import CalLampPower
from kpf.calbench.SetCalSource import SetCalSource
from kpf.fiu.ConfigureFIU import ConfigureFIU
from kpf.fiu.SetCurrentBase import SetCurrentBase
from kpf.fiu.StartTipTilt import StartTipTilt
from kpf.spectrograph.SetSourceSelectShutters import SetSourceSelectShutters
from kpf.spectrograph.SetTriggeredDetectors import SetTriggeredDetectors
from kpf.spectrograph.WaitForReady import WaitForReady


class ConfigureForScience(KPFTranslatorFunction):
    '''Script which configures the instrument for Science observations.

    - Sets octagon / simulcal source
    - Sets source select shutters

    This must have arguments as input, either from a file using the `-f` command
    line tool, or passed in from the execution engine.

    Can be called by `ddoi_script_functions.configure_for_science`.

    ARGS:
    =====
    None
    '''
    @classmethod
    @obey_scriptrun
    def pre_condition(cls, OB, logger, cfg):
        check_input(OB, 'Template_Name', allowed_values=['kpf_sci'])
        check_input(OB, 'Template_Version', version_check=True, value_min='0.5')
        return True

    @classmethod
    def perform(cls, OB, logger, cfg):
        log.info('-------------------------')
        log.info(f"Running {cls.__name__}")
        for key in OB:
            if key not in ['SEQ_Observations']:
                log.debug(f"  {key}: {OB[key]}")
            else:
                log.debug(f"  {key}:")
                for entry in OB[key]:
                    log.debug(f"    {entry}")
        log.info('-------------------------')

        # Start tip tilt loops
        if OB['GuideMode'] in ['manual', 'auto']:
            log.info(f"Starting tip tilt loops")
            SetCurrentBase.execute(OB)
            StartTipTilt.execute({})
            tick = datetime.now()
        elif OB['GuideMode'] in ['off', 'telescope']:
            log.info('GuideMode in OB is "off", not starting tip tilt loops')

        # Set Octagon
        kpfconfig = ktl.cache('kpfconfig')
        calsource = kpfconfig['SIMULCALSOURCE'].read()
        octagon = ktl.cache('kpfcal', 'OCTAGON').read()
        log.debug(f"Current OCTAGON = {octagon}, desired = {calsource}")
        if octagon != calsource:
            log.info(f"Set CalSource/Octagon: {calsource}")
            SetCalSource.execute({'CalSource': calsource, 'wait': False})

        exposestatus = ktl.cache('kpfexpose', 'EXPOSE')
        if exposestatus.read() != 'Ready':
            log.info(f"Waiting for kpfexpose to be Ready")
            WaitForReady.execute({})
            log.info(f"Readout complete")
        # Set source select shutters
        log.info(f"Set Source Select Shutters")
        SetSourceSelectShutters.execute({'SSS_Science': True,
                                         'SSS_Sky': True,
                                         'SSS_SoCalSci': False,
                                         'SSS_SoCalCal': False,
                                         'SSS_CalSciSky': False})

        # Set Triggered Detectors
        OB['TriggerGuide'] = (OB.get('GuideMode', 'off') != 'off')
        SetTriggeredDetectors.execute(OB)

        # Make sure tip tilt loops have had time to close
        if OB['GuideMode'] in ['manual', 'auto']:
            tock = datetime.now()
            time_passed = (tock - tick).total_seconds()
            tt_close_time = cfg.get('times', 'tip_tilt_close_time', fallback=3)
            sleep_time = tt_close_time - time_passed
            if sleep_time > 0:
                log.info(f"Sleeping {sleep_time:.1f} seconds to allow loops to close")
                time.sleep(sleep_time)

    @classmethod
    def post_condition(cls, OB, logger, cfg):
        return True
