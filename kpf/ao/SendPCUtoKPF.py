import time
import ktl

from kpf import log, cfg, check_input
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
        ao = ktl.cache('ao')
        success = ktl.waitfor("($ao.PCSFSTST == INPOS)", timeout=120)
        if success is False:
            raise FailedPreCondition('PCU is in motion')
        success = ktl.waitfor("($ao.PCSFNAME == home)", timeout=120)
        if success is False:
            raise FailedPreCondition('PCU must be at home before moving to KPF')

    @classmethod
    def perform(cls, args):
        PCSstagekw = ktl.cache('ao', 'PCSFNAME')
        log.info(f"Sending PCU to KPF")
        PCSstagekw.write('kpf')
        shim_time = cfg.getfloat('times', 'ao_pcu_shim_time', fallback=5)
        time.sleep(shim_time)

    @classmethod
    def post_condition(cls, args):
        PCSstagekw = ktl.cache('ao', 'PCSFSTST')
        timeout = cfg.getfloat('times', 'ao_pcu_move_time', fallback=150)
        success = PCSstagekw.waitfor("== INPOS", timeout=timeout)
        if success is False:
            raise FailedToReachDestination(PCSstagekw.read(), 'kpf')
