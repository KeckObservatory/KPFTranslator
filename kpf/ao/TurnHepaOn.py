import ktl

import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)


class TurnHepaOn(KPFTranslatorFunction):
    '''Turn HEPA Filter system on
    
    ARGS: None
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        ao = ktl.cache('ao')
        log.debug('Setting AO HEPA filter to on')
        ao['OBHPAON'].write(1)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        success = ktl.waitfor('($ao.OBHPASTA == on)', timeout=3)
        if success is not True:
            ao = ktl.cache('ao')
            raise FailedToReachDestination(ao['OBHPASTA'].read(), 'on')
