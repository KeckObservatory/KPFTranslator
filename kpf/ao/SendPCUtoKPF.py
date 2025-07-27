import time
import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


class SendPCUtoKPF(KPFFunction):
    '''Send the PCU stage to the "kpf" named position.

    KTL Keywords Used:

    - `ao.PCSFNAME`
    - `ao.PCSFSTST`
    '''
    @classmethod
    def pre_condition(cls, args):
        PCSFSTST = ktl.cache('ao', 'PCSFSTST')
        PCSFNAME = ktl.cache('ao', 'PCSFNAME')
        if PCSFSTST.waitFor('!= "FAULT"', timeout=1) != True:
            raise FailedPreCondition('PCSFSTST is faulted')
        if PCSFSTST.waitfor("== 'INPOS'", timeout=120) == False:
            raise FailedPreCondition('PCU is in motion')
        if PCSFNAME.waitfor("== 'home'", timeout=120) == False:
            raise FailedPreCondition('PCU must be at home before moving to KPF')

    @classmethod
    def perform(cls, args):
        PCSFNAME = ktl.cache('ao', 'PCSFNAME')
        log.info(f"Sending PCU to KPF")
        PCSFNAME.write('kpf')
        shim_time = cfg.getfloat('times', 'ao_pcu_shim_time', fallback=5)
        time.sleep(shim_time)

    @classmethod
    def post_condition(cls, args):
        PCSFSTST = ktl.cache('ao', 'PCSFSTST')
        timeout = cfg.getfloat('times', 'ao_pcu_move_time', fallback=150)
        success = PCSFSTST.waitfor("== INPOS", timeout=timeout)
        if success is False:
            raise FailedToReachDestination(PCSFSTST.read(), 'kpf')
