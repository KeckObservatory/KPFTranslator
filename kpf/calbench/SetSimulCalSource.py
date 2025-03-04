from pathlib import Path

import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.calbench.SetCalSource import SetCalSource


##-------------------------------------------------------------------------
## SetSimulCalSource
##-------------------------------------------------------------------------
class SetSimulCalSource(KPFFunction):
    '''Set the simultaneous calibration source based on the
    kpfconfig.SIMULCALSOURCE keyword.
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        calsource = ktl.cache('kpfconfig', 'SIMULCALSOURCE').read()
        octagon = ktl.cache('kpfcal', 'OCTAGON').read()
        log.debug(f"Current OCTAGON = {octagon}, desired = {calsource}")
        if octagon != calsource:
            log.info(f"Set CalSource/Octagon: {calsource}")
            SetCalSource.execute({'CalSource': calsource, 'wait': False})

    @classmethod
    def post_condition(cls, args):
        pass
