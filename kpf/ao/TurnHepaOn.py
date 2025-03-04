import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


class TurnHepaOn(KPFFunction):
    '''Turn HEPA Filter system on

    KTL Keywords Used:

    - `ao.OBHPAON`
    - `ao.OBHPASTA`
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        ao = ktl.cache('ao')
        log.debug('Setting AO HEPA filter to on')
        ao['OBHPAON'].write(1)

    @classmethod
    def post_condition(cls, args):
        success = ktl.waitfor('($ao.OBHPASTA == on)', timeout=3)
        if success is not True:
            ao = ktl.cache('ao')
            raise FailedToReachDestination(ao['OBHPASTA'].read(), 'on')
