import os
from time import sleep
from packaging import version
from pathlib import Path
import numpy as np

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.scripts import (register_script, obey_scriptrun, check_scriptstop,
                         add_script_log)
from kpf.calbench.CalLampPower import CalLampPower
from kpf.calbench.SetLFCtoAstroComb import SetLFCtoAstroComb
from kpf.fiu.ConfigureFIU import ConfigureFIU
from kpf.spectrograph.SetTriggeredDetectors import SetTriggeredDetectors
from kpf.spectrograph.WaitForReady import WaitForReady


class ConfigureForCalibrations(KPFTranslatorFunction):
    '''Script which configures the instrument for Cal OBs.

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
        check_input(OB, 'Template_Name', allowed_values=['kpf_cal'])
        check_input(OB, 'Template_Version', version_check=True, value_min='0.5')
        return True

    @classmethod
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
            if lamp == 'LFCFiber':
                SetLFCtoAstroComb.execute({})

        log.debug(f"Ensuring back illumination LEDs are off")
        CalLampPower.execute({'lamp': 'ExpMeterLED', 'power': 'off'})
        CalLampPower.execute({'lamp': 'CaHKLED', 'power': 'off'})
        CalLampPower.execute({'lamp': 'SciLED', 'power': 'off'})
        CalLampPower.execute({'lamp': 'SkyLED', 'power': 'off'})

        log.info(f"Configuring FIU")
        ConfigureFIU.execute({'mode': 'Calibration'})
        log.info(f"Set Detector List")
        WaitForReady.execute({})
        SetTriggeredDetectors.execute(OB)

    @classmethod
    def post_condition(cls, OB, logger, cfg):
        return True
