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


class WaitForConfigureScience(KPFTranslatorFunction):
    '''Script which waits for the instrument to be configured for Science observations.

    ARGS:
    =====
    None
    '''
    @classmethod
    def pre_condition(cls, OB, logger, cfg):
        check_input(OB, 'Template_Name', allowed_values=['kpf_sci'])
        check_input(OB, 'Template_Version', version_check=True, value_min='0.5')

    @classmethod
    def perform(cls, OB, logger, cfg):
        kpfconfig = ktl.cache('kpfconfig')
        calsource = kpfconfig['SIMULCALSOURCE'].read()
        WaitForCalSource.execute({'CalSource': calsource})
        WaitForConfigureFIU.execute({'mode': 'Observing'})
        WaitForReady.execute({})

    @classmethod
    def post_condition(cls, OB, logger, cfg):
        pass
