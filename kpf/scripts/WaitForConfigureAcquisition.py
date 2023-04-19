import os
from time import sleep
from packaging import version
from pathlib import Path
import yaml
import numpy as np

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.fiu.WaitForConfigureFIU import WaitForConfigureFIU


class WaitForConfigureAcquisition(KPFTranslatorFunction):
    '''Script which waits for the configure for Acquisition step.

    Can be called by `ddoi_script_functions.waitfor_configure_for_acquisition`.

    ARGS:
    =====
    None
    '''
    @classmethod
    def pre_condition(cls, OB, logger, cfg):
        check_input(OB, 'Template_Name', allowed_values=['kpf_sci'])
        check_input(OB, 'Template_Version', version_check=True, value_min='0.5')
        return True

    @classmethod
    def perform(cls, OB, logger, cfg):
        WaitForConfigureFIU.execute({'mode': 'Observing', 'wait': False})

    @classmethod
    def post_condition(cls, OB, logger, cfg):
        return True
