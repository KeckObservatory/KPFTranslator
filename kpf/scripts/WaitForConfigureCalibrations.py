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
from ..calbench.WaitForCalSource import WaitForCalSource
from ..fiu.WaitForConfigureFIU import WaitForConfigureFIU
from ..spectrograph.WaitForReady import WaitForReady


class WaitForConfigureCalibrations(KPFTranslatorFunction):
    '''Script which waits for the instrument to be configured for calibrations.

    Can be called by `ddoi_script_functions.waitfor_configure_for_science`.

    ARGS:
    =====
    None
    '''
    @classmethod
    def pre_condition(cls, OB, logger, cfg):
        check_input(OB, 'Template_Name', allowed_values=['kpf_cal'])
        check_input(OB, 'Template_Version', version_check=True, value_min='0.5')
        return True

    @classmethod
    def perform(cls, OB, logger, cfg):
        WaitForCalSource.execute(OB)
        WaitForConfigureFIU.execute({'mode': 'Calibration'})
        WaitForReady.execute({})

    @classmethod
    def post_condition(cls, OB, logger, cfg):
        return True
