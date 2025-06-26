import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


class TurnHepaOff(KPFFunction):
    '''Turn HEPA Filter system off

    KTL Keywords Used:

    - `ao.OBHPAON`
    - `ao.OBHPASTA`
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        OBHPAON = ktl.cache('ao', 'OBHPAON')
        log.debug('Setting AO HEPA filter to off')
        OBHPAON.write(0)

    @classmethod
    def post_condition(cls, args):
        OBHPASTA = ktl.cache('ao', 'OBHPASTA')
        if OBHPASTA.waitfor('== "off"', timeout=3) is not True:
            raise FailedToReachDestination(OBHPASTA.read(), 'off')
