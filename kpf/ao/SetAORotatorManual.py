import ktl

from kpf import log, cfg, check_input
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
        ao = ktl.cache('ao')
        log.debug("Setting AO rotator to manual mode")
        ao['OBRTDSRC'].write('0')
        ao['OBRTMOVE'].write('1')

    @classmethod
    def post_condition(cls, args):
        success = ktl.waitfor('($ao.OBRTDSRC == manual)', timeout=3)
        if success is not True:
            ao = ktl.cache('ao')
            raise FailedToReachDestination(ao['OBRTDSRC'].read(), 'manual')
