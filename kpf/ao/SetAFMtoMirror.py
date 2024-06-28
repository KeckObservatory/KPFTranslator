import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class SetAFMtoMirror(KPFTranslatorFunction):
    '''Set AFM to Mirror so ACAM sees light

    KTL Keywords Used:

    - `ao.OBAMNAME`
    - `ao.OBAMSLEW`
    - `ao.OBAMSTST`
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        pass

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

