import os
from time import sleep
from packaging import version
from pathlib import Path
import numpy as np

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)
from . import register_script, obey_scriptrun, check_scriptstop, add_script_log
from ..calbench.CalLampPower import CalLampPower
from ..fiu.ConfigureFIU import ConfigureFIU
from ..spectrograph.SetTriggeredDetectors import SetTriggeredDetectors


class ConfigureForCalibrations(KPFTranslatorFunction):
    '''Script which configures the instrument for Cal OBs.
    
    Can be called by `ddoi_script_functions.configure_for_science`.
    '''
    @classmethod
    @obey_scriptrun
    def pre_condition(cls, OB, logger, cfg):
        check_input(OB, 'Template_Name', allowed_values=['kpf_cal'])
        check_input(OB, 'Template_Version', version_check=True, value_min='0.5')
        return True

    @classmethod
    @add_script_log(Path(__file__).name.replace(".py", ""))
    def perform(cls, OB, logger, cfg):
        log.info('-------------------------')
        log.info(f"Running {cls.__name__}")
        for key in OB:
            if key not in ['SEQ_Darks', 'SEQ_Calibrations']:
                log.debug(f"  {key}: {OB[key]}")
            else:
                log.debug(f"  {key}:")
                for entry in OB[key]:
                    log.debug(f"    {entry}")
        log.info('-------------------------')

        # Power up needed lamps
        sequence = OB.get('SEQ_Calibrations')
        lamps = set([x['CalSource'] for x in sequence if x['CalSource'] != 'Home'])
        for lamp in lamps:
            if lamp in ['Th_daily', 'Th_gold', 'U_daily', 'U_gold',
                        'BrdbandFiber', 'WideFlat']:
                CalLampPower.execute({'lamp': lamp, 'power': 'on'})

        log.debug(f"Ensuring back illumination LEDs are off")
        CalLampPower.execute({'lamp': 'ExpMeterLED', 'power': 'off'})
        CalLampPower.execute({'lamp': 'CaHKLED', 'power': 'off'})
        CalLampPower.execute({'lamp': 'SciLED', 'power': 'off'})
        CalLampPower.execute({'lamp': 'SkyLED', 'power': 'off'})

        log.info(f"Configuring FIU")
        ConfigureFIU.execute({'mode': 'Calibration'})
        log.info(f"Set Detector List")
        SetTriggeredDetectors.execute(OB)

    @classmethod
    def post_condition(cls, OB, logger, cfg):
        return True
