import os
from time import sleep
from packaging import version
from pathlib import Path
import numpy as np

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.scripts import (register_script, obey_scriptrun, check_scriptstop,
                         add_script_log)
from kpf.calbench.CalLampPower import CalLampPower
from kpf.calbench.IsCalSourceEnabled import IsCalSourceEnabled
from kpf.fiu.ConfigureFIU import ConfigureFIU
from kpf.spectrograph.SetTriggeredDetectors import SetTriggeredDetectors
from kpf.spectrograph.WaitForReady import WaitForReady


class ConfigureForCalibrations(KPFTranslatorFunction):
    '''Script which configures the instrument for Cal OBs.

    ARGS:
    =====
    :calibrations: `list` A list of `kpf.ObservingBlocks.Calibration.Calibration`
                   OB components.
    '''
    @classmethod
    @obey_scriptrun
    def pre_condition(cls, calibrations):
        pass # OB should already have been validated by RunOB

    @classmethod
    def simple_perform(cls, calibrations):
        log.info('-------------------------')
        log.info(f"Running {cls.__name__}")
        for i,calibration in enumerate(calibrations):
            log.debug(f"Calibration {i+1}/{len(calibrations)}")
            for key in calibration:
                log.debug(f"  {key}: {calibration.get(key)}")
        log.info('-------------------------')

        check_scriptstop()

        # Power on needed lamps
        lamps = set([c.get('CalSource') for c in calibrations])
        for lamp in lamps:
            if IsCalSourceEnabled.execute({'CalSource': lamp}) == True:
                if lamp in ['Th_daily', 'Th_gold', 'U_daily', 'U_gold',
                            'BrdbandFiber', 'WideFlat']:
                    CalLampPower.execute({'lamp': lamp, 'power': 'on'})

        # Set back illumination LEDs to off
        log.debug(f"Ensuring back illumination LEDs are off")
        CalLampPower.execute({'lamp': 'ExpMeterLED', 'power': 'off'})
        CalLampPower.execute({'lamp': 'CaHKLED', 'power': 'off'})
        CalLampPower.execute({'lamp': 'SciLED', 'power': 'off'})
        CalLampPower.execute({'lamp': 'SkyLED', 'power': 'off'})

        check_scriptstop()

        # Configure FIU
        log.info(f"Configuring FIU")
        ConfigureFIU.execute({'mode': 'Calibration'})

        check_scriptstop()

    @classmethod
    def perform(cls, calibrations):
        try:
            cls.simple_perform(calibrations)
        except Exception as e:
            log.error('Running CleanupAfterCalibrations and exiting')
            CleanupAfterCalibrations.execute([calibration])
            raise e

    @classmethod
    def post_condition(cls, OB, logger, cfg):
        pass
