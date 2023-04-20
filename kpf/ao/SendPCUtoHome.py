import time
import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class SendPCUtoHome(KPFTranslatorFunction):
    '''Send the PCU stage to the "home" named position.
    
    ARGS:
    =====
    None
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        ao = ktl.cache('ao')
        log.info(f"Sending PCU to Home")
        ao['PCSFNAME'].write('home')
        shim_time = cfg.getfloat('times', 'ao_pcu_shim_time', fallback=5)
        time.sleep(shim_time)
        timeout = cfg.getfloat('times', 'ao_pcu_move_time', fallback=150)
        success = ktl.waitfor("($ao.PCSFSTST == INPOS)", timeout=timeout)
        if success is False:
            raise FailedToReachDestination(ao['PCSFNAME'].read(), 'home')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True
