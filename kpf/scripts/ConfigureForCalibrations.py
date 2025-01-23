import os
from time import sleep
from packaging import version
from pathlib import Path
import numpy as np

import ktl

from kpf.KPFTranslatorFunction import KPFScript
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.scripts import (register_script, obey_scriptrun, check_scriptstop,
                         add_script_log)
from kpf.ObservingBlocks.Calibration import Calibration

from kpf.calbench.CalLampPower import CalLampPower
from kpf.calbench.IsCalSourceEnabled import IsCalSourceEnabled
from kpf.fiu.ConfigureFIU import ConfigureFIU
from kpf.spectrograph.SetTriggeredDetectors import SetTriggeredDetectors
from kpf.spectrograph.WaitForReady import WaitForReady


class ConfigureForCalibrations(KPFScript):
    '''Script which configures the instrument for Cal OBs.

    ARGS:
    =====
    * __OB__ - `ObservingBlock` or `dict` A valid observing block (OB).
    '''
    @classmethod
    @obey_scriptrun
    def pre_condition(cls, args, OB=None):
        pass

    @classmethod
    def perform(cls, args, OB=None):
        if isinstance(OB, dict):
            OB = ObservingBlock(OB)
        calibrations = OB.Calibrations
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
    def post_condition(cls, args, OB=None):
        pass
