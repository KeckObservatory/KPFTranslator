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
        heartbeat = ktl.cache('kpfmon', 'NE_HB_MENLO')
        success = heartbeat.waitFor('== "OK"', timeout=3)
        if success is False:
            raise FailedPreCondition(f"Menlo heartbeat is not OK: {heartbeat.read()}")

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
        LFCready = ktl.cache('kpfmon', 'LFCREADYSTA')
        timeout = cfg.getfloat('times', 'LFC_startup_time', fallback=60)
        success = LFCready.waitFor('== "OK"', timeout=timeout)
        if success is not True:
            raise FailedPostCondition('kpfmon.LFCREADYSTA is not OK')
