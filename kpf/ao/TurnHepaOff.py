import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)


class TurnHepaOff(KPFTranslatorFunction):
    '''Turn HEPA Filter system off
    
    ARGS: None
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        ao = ktl.cache('ao')
        log.debug('Setting AO HEPA filter to off')
        ao['OBHPAON'].write(0)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        success = ktl.waitfor('($ao.OBHPASTA == off)', timeout=3)
        if success is not True:
            ao = ktl.cache('ao')
            raise FailedToReachDestination(ao['OBHPASTA'].read(), 'off')
