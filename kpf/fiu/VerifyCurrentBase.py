import numpy as np

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class VerifyCurrentBase(KPFTranslatorFunction):
    '''Check whether the tip tilt system's target pixel (kpffiu.CURRENT_BASE)
    is consistent with the selected pointing origin (dcs.PONAME)

    ARGS:
    =====
    None
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def perform(cls, args, logger, cfg):
        ponamekw = ktl.cache('dcs1', 'PONAME')
        poname = ponamekw.read().upper()

        kpfguide = ktl.cache('kpfguide')
        current_base = kpfguide['CURRENT_BASE'].read(binary=True)
        science_base = kpfguide['SCIENCE_BASE'].read(binary=True)
        sky_base = kpfguide['SKY_BASE'].read(binary=True)

        science_match = np.all(np.isclose(current_base, science_base, atol=0.01))
        sky_match = np.all(np.isclose(current_base, sky_base, atol=0.01))
        msg = f"CURRENT_BASE="
        if science_match:
            log.debug(f"CURRENT_BASE is science fiber, PO = {poname}")
            msg += 'SCIENCE_BASE'
        elif sky_match:
            log.debug(f"CURRENT_BASE is sky fiber, PO = {poname}")
            msg += 'SKY_BASE'
        else:
            log.debug(f"CURRENT_BASE is {current_base}, PO = {poname}")
            msg += 'custom'

        poname_match = (science_match and poname == 'KPF')\
                       or (sky_match and poname == 'SKY')
        if poname_match:
            msg += f" which is consistent with PONAME={poname}"
            log.debug(msg)
        else:
            msg += f" which is NOT consistent with PONAME={poname}"
            log.error(msg)
        print(msg)

        return poname_match

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass