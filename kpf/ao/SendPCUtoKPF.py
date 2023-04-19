import time
import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class SendPCUtoKPF(KPFTranslatorFunction):
    '''Send the PCU stage to the "kpf" named position.
    
    ARGS:
    =====
    None
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        ao = ktl.cache('ao')
        success = ktl.waitfor("($ao.PCSFSTST == INPOS)", timeout=120)
        if success is False:
            raise FailedPreCondition('PCU is in motion')
        success = ktl.waitfor("($ao.PCSFNAME == home)", timeout=120)
        if success is False:
            raise FailedPreCondition('PCU must be at home before moving to KPF')
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        ao = ktl.cache('ao')
        log.info(f"Sending PCU to KPF")
        ao['PCSFNAME'].write('kpf')
        shim_time = cfg.get('times', 'ao_pcu_shim_time', fallback=5)
        time.sleep(shim_time)
        timeout = cfg.get('times', 'ao_pcu_move_time', fallback=150)
        success = ktl.waitfor("($ao.PCSFSTST == INPOS)", timeout=timeout)
        if success is False:
            raise FailedToReachDestination(ao['PCSFNAME'].read(), 'kpf')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True
