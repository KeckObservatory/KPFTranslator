import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


class TurnLightSourceOff(KPFFunction):
    '''Turn K1 AO light source off

    KTL Keywords Used:

    - `ao.OBSWON`
    - `ao.OBSWSTA`
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        ao = ktl.cache('ao')
        log.debug('Turning AO light source off')
        ao['OBSWON'].write(0)
#         ao['ASCONFIG'].write('OFF')

    @classmethod
    def post_condition(cls, args):
        success = ktl.waitfor('($ao.OBSWSTA == off)', timeout=3)
        if success is not True:
            ao = ktl.cache('ao')
            raise FailedToReachDestination(ao['OBSWSTA'].read(), 'off')
