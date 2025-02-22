import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class SetAODCStoSIM(KPFTranslatorFunction):
    '''Set AO in AO DCS sim mode, so AO doesn't communicate with telescope

    KTL Keywords Used:

    - `ao.AODCSSIM`
    - `ao.AOCOMSIM`
    - `ao.AODCSSFP`
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def perform(cls, args, logger, cfg):
        ao = ktl.cache('ao')
        log.debug("Setting AO DCS to Sim")
        ao['AODCSSIM'].write('1')
        ao['AOCOMSIM'].write('1')
        ao['AODCSSFP'].write('0')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        ao = ktl.cache('ao')
        aodcssim_success = ktl.waitfor('($ao.AODCSSIM == enabled)', timeout=3)
        if not aodcssim_success:
            raise FailedToReachDestination(ao['AODCSSIM'].read(), 'enabled')
        aocomsim_success = ktl.waitfor('($ao.AOCOMSIM == enabled)', timeout=3)
        if not aocomsim_success:
            raise FailedToReachDestination(ao['AOCOMSIM'].read(), 'enabled')
        aodcssfp_success = ktl.waitfor('($ao.AODCSSFP == disabled)', timeout=3)
        if not aodcssfp_success:
            raise FailedToReachDestination(ao['AODCSSFP'].read(), 'disabled')
