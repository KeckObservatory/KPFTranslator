import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class TurnLightSourceOff(KPFTranslatorFunction):
    '''# Description
    Turn K1 AO light source off

    ## KTL Keywords Used

    - `ao.OBSWON`
    - `ao.OBSWSTA`

    ## Scripts Called

    None

    ## Parameters

    None
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def perform(cls, args, logger, cfg):
        ao = ktl.cache('ao')
        log.debug('Turning AO light source off')
        ao['OBSWON'].write(0)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        success = ktl.waitfor('($ao.OBSWSTA == off)', timeout=3)
        if success is not True:
            ao = ktl.cache('ao')
            raise FailedToReachDestination(ao['OBSWSTA'].read(), 'off')
