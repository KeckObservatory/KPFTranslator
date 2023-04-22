import time

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class SetLFCtoAstroComb(KPFTranslatorFunction):
    '''Set the Laser Frequency Comb (LFC) to "AstroComb" mode. This should
    be used during operation of the LFC.

    ARGS:
    =====
    None
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def perform(cls, args, logger, cfg):
        lfc_mode = ktl.cache('kpfcal', 'OPERATIONMODE')
        log.info('Setting LFC to AstroComb')
        lfc_mode.write('AstroComb')
        time_shim = cfg.getfloat('times', 'LFC_shim_time', fallback=10)
        time.sleep(time_shim)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        '''Verifies that kpfmon shows no errors.
        '''
        expr = f"($kpfmon.LFCREADYSTA == 'OK')"
        timeout = cfg.getfloat('times', 'LFC_startup_time', fallback=60)
        success = ktl.waitFor(expr, timeout=timeout)
        if success is not True:
            raise FailedPostCondition('kpfmon.LFCREADYSTA is not OK')
