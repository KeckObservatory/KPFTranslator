import time
import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class SendPCUtoHome(KPFTranslatorFunction):
    '''Send the PCU stage to the "home" named position.

    KTL Keywords Used:

    - `ao.PCSFNAME`
    - `ao.PCSFSTST`
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        PCSFSTST = ktl.cache('ao', 'PCSFSTST')
        success = PCSFSTST.waitFor('!= "FAULT"')
        if success is not True:
            raise FailedPreCondition('PCSFSTST is faulted')

    @classmethod
    def perform(cls, args, logger, cfg):
        PCSstagekw = ktl.cache('ao', 'PCSFNAME')
        log.info(f"Sending PCU to Home")
        PCSstagekw.write('home')
        shim_time = cfg.getfloat('times', 'ao_pcu_shim_time', fallback=5)
        time.sleep(shim_time)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        PCSstagekw = ktl.cache('ao', 'PCSFSTST')
        timeout = cfg.getfloat('times', 'ao_pcu_move_time', fallback=150)
        success = PCSstagekw.waitfor("== INPOS", timeout=timeout)
        if success is False:
            raise FailedToReachDestination(PCSstagekw.read(), 'home')
