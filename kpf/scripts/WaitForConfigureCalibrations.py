import os
from time import sleep
from packaging import version
from pathlib import Path
import numpy as np

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.calbench.WaitForCalSource import WaitForCalSource
from kpf.fiu.WaitForConfigureFIU import WaitForConfigureFIU
from kpf.spectrograph.WaitForReady import WaitForReady


class WaitForConfigureCalibrations(KPFTranslatorFunction):
    '''Script which waits for the instrument to be configured for calibrations.

    ARGS:
    =====
    None
    '''
    @classmethod
    def pre_condition(cls, OB, logger, cfg):
        check_input(OB, 'Template_Name', allowed_values=['kpf_cal'])
        check_input(OB, 'Template_Version', version_check=True, value_min='0.5')

    @classmethod
    def perform(cls, OB, logger, cfg):
        WaitForCalSource.execute(OB)
        WaitForConfigureFIU.execute({'mode': 'Calibration'})
        WaitForReady.execute({})

    @classmethod
    def post_condition(cls, OB, logger, cfg):
        pass
