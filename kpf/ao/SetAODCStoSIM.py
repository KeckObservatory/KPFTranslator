import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


class SetAODCStoSIM(KPFFunction):
    '''Set AO in AO DCS sim mode, so AO doesn't communicate with telescope

    KTL Keywords Used:

    - `ao.AODCSSIM`
    - `ao.AOCOMSIM`
    - `ao.AODCSSFP`
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        AODCSSIM = ktl.cache('ao', 'AODCSSIM')
        AOCOMSIM = ktl.cache('ao', 'AOCOMSIM')
        AODCSSFP = ktl.cache('ao', 'AODCSSFP')
        log.debug("Setting AO DCS to Sim")
        AODCSSIM.write('1')
        AOCOMSIM.write('1')
        AODCSSFP.write('0')

    @classmethod
    def post_condition(cls, args):
        AODCSSIM = ktl.cache('ao', 'AODCSSIM')
        if not AODCSSIM.waitfor('== "enabled"', timeout=3):
            raise FailedToReachDestination(AODCSSIM.read(), 'enabled')
        AOCOMSIM = ktl.cache('ao', 'AOCOMSIM')
        if not AOCOMSIM.waitfor('== "enabled"', timeout=3):
            raise FailedToReachDestination(AOCOMSIM.read(), 'enabled')
        AODCSSFP = ktl.cache('ao', 'AODCSSFP')
        if not AODCSSFP.waitfor('== "disabled"', timeout=3):
            raise FailedToReachDestination(AODCSSFP.read(), 'disabled')
