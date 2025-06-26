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
        OBSWON = ktl.cache('ao', 'OBSWON')
        log.debug('Turning AO light source off')
        OBSWON.write(0)

    @classmethod
    def post_condition(cls, args):
        OBSWSTA = ktl.cache('ao', 'OBSWSTA')
        if OBSWSTA.waitfor('== "off"', timeout=3) is not True:
            raise FailedToReachDestination(OBSWSTA.read(), 'off')
