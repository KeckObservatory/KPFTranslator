import os
from time import sleep
from packaging import version
from pathlib import Path
import numpy as np

import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.calbench.WaitForCalSource import WaitForCalSource
from kpf.fiu.WaitForConfigureFIU import WaitForConfigureFIU
from kpf.spectrograph.WaitForReady import WaitForReady


class WaitForConfigureScience(KPFScript):
    '''Script which waits for the instrument to be configured for Science
    observations.

    KTL Keywords Used:

    - `kpfconfig.SIMULCALSOURCE`

    Functions Called:

    - `kpf.calbench.WaitForCalSource`
    - `kpf.fiu.WaitForConfigureFIU`
    - `kpf.spectrograph.WaitForReady`
    '''
    @classmethod
    def pre_condition(cls, args, OB=None):
        pass

    @classmethod
    def perform(cls, args, OB=None):
        kpfconfig = ktl.cache('kpfconfig')
        calsource = kpfconfig['SIMULCALSOURCE'].read()
        WaitForCalSource.execute({'CalSource': calsource})
        WaitForConfigureFIU.execute({'mode': 'Observing'})
        WaitForReady.execute({})

    @classmethod
    def post_condition(cls, args, OB=None):
        pass
