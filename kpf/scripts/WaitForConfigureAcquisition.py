import os
from time import sleep
from packaging import version
from pathlib import Path
import yaml
import numpy as np

import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.fiu.WaitForConfigureFIU import WaitForConfigureFIU


class WaitForConfigureAcquisition(KPFScript):
    '''Script which waits for the configure for Acquisition step.

    Functions Called:

    - `kpf.fiu.WaitForConfigureFIU`
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
