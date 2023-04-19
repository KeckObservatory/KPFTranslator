import time

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class SetLFCtoStandbyHigh(KPFTranslatorFunction):
    '''Set the Laser Frequency Comb (LFC) to "StandbyHigh" mode. This is the
    mode which should be set after operation of the LFC for science is complete.


    ARGS:
    =====
    None
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        lfc_mode = ktl.cache('kpfcal', 'OPERATIONMODE')
        log.info('Setting LFC to StandbyHigh')
        lfc_mode.write('StandbyHigh')
        time_shim = cfg.get('times', 'LFC_shim_time', fallback=10)
        time.sleep(time_shim)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        '''Verifies that kpfmon shows no errors.
        '''
        expr = f"($kpfmon.LFCREADYSTA == 'OK')"
        timeout = cfg.get('times', 'LFC_startup_time', fallback=60)
        success = ktl.waitFor(expr, timeout=timeout)
        if success is not True:
            raise FailedPostCondition('kpfmon.LFCREADYSTA is not OK')
        return True #success
