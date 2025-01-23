import os
from time import sleep
from packaging import version
from pathlib import Path
import yaml
import numpy as np

import ktl

from kpf.KPFTranslatorFunction import KPFScript
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.fiu.WaitForConfigureFIU import WaitForConfigureFIU


class WaitForConfigureAcquisition(KPFTranslatorFunction):
    '''Script which waits for the configure for Acquisition step.

    ARGS:
    =====
    None
    '''
    @classmethod
    def pre_condition(cls, args, OB=None):
        pass

    @classmethod
    def perform(cls, args, OB=None):
        WaitForConfigureFIU.execute({'mode': 'Observing'})

    @classmethod
    def post_condition(cls, args, OB=None):
        pass
