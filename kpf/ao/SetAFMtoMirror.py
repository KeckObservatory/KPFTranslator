import ktl

import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)


class SetAFMtoMirror(KPFTranslatorFunction):
    '''Set AFM to Mirror so ACAM sees light
    
    ARGS: None
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        ao = ktl.cache('ao')
        log.debug(f"Setting AFM to Mirror")
        ao['OBAMNAME'].write('Mirror')
        ao['OBAMSLEW'].write('1')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        expr = '($ao.OBAMSTST == INPOS) and ($ao.OBAMNAME == Mirror)'
        aoamstst_success = ktl.waitfor(expr, timeout=60)
        if not aoamstst_success:
            ao = ktl.cache('ao')
            FailedToReachDestination(ao['OBAMNAME'].read(), 'Mirror')
        return True
