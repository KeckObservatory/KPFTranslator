import os
from time import sleep
from packaging import version
from pathlib import Path
import numpy as np

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)
from . import register_script, obey_scriptrun, check_scriptstop
from ..calbench.CalLampPower import CalLampPower
from ..spectrograph.SetObject import SetObject
from ..spectrograph.WaitForReady import WaitForReady


## Create special script logger object
from . import get_script_log
this_file_name = Path(__file__).name.replace(".py", "")
log = get_script_log(this_file_name)


class CleanupAfterCalibrations(KPFTranslatorFunction):
    '''Script which cleans up after Cal OBs.
    
    Can be called by `ddoi_script_functions.post_observation_cleanup`.
    '''
    @classmethod
    @obey_scriptrun
    def pre_condition(cls, OB, logger, cfg):
        check_input(OB, 'Template_Name', allowed_values=['kpf_cal'])
        check_input(OB, 'Template_Version', version_check=True, value_min='0.3')
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

        # Power off lamps
        sequence = OB.get('SEQ_Calibrations')
        lamps = set([x['CalSource'] for x in sequence if x['CalSource'] != 'Home'])
        for lamp in lamps:
            if lamp in ['Th_daily', 'Th_gold', 'U_daily', 'U_gold',
                        'BrdbandFiber', 'WideFlat']:
                CalLampPower.execute({'lamp': lamp, 'power': 'off'})

        # Set OBJECT back to empty string
        WaitForReady.execute({})
        SetObject.execute({'Object': ''})

    @classmethod
    def post_condition(cls, OB, logger, cfg):
        return True
