import time

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class WaitForLFCReady(KPFTranslatorFunction):
    '''Wait for the Laser Frequency Comb (LFC) to be ready and in "AstroComb"
    mode

    ARGS:
    =====
    None
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def perform(cls, args, logger, cfg):
        expr = f"($kpfmon.HB_MENLOSTA == 'OK')"
        expr += f"and ($kpfmon.LFCREADYSTA == 'OK')"
        expr += f"and ($kpfcal.WOBBLE == 'False')"
        expr += f"and ($kpfcal.OPERATIONMODE == 'AstroComb')"
        expr += f"and ($kpfcal.SPECFLAT == 'True')"
        timeout = cfg.getfloat('times', 'LFC_startup_time', fallback=300)
        success = ktl.waitFor(expr, timeout=timeout)
        return success

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass
