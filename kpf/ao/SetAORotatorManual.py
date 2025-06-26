import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


class SetAORotatorManual(KPFFunction):
    '''AO rotator needs to be in the Manual mode before observing.

    KTL Keywords Used: 

    - `ao.OBRTDSRC`
    - `ao.OBRTMOVE`
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        OBRTDSRC = ktl.cache('ao', 'OBRTDSRC')
        OBRTMOVE = ktl.cache('ao', 'OBRTMOVE')
        log.debug("Setting AO rotator to manual mode")
        OBRTDSRC.write('0')
        OBRTMOVE.write('1')

    @classmethod
    def post_condition(cls, args):
        OBRTDSRC = ktl.cache('ao', 'OBRTDSRC')
        if OBRTDSRC.waitfor('== "manual"', timeout=3) is not True:
            raise FailedToReachDestination(OBRTDSRC.read(), 'manual')
