import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import log


class SetAODCStoSIM(KPFTranslatorFunction):
    '''Set AO in AO DCS sim mode, so AO doesn't communicate with telescope
    
    ARGS: None
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        ao = ktl.cache('ao')
        log.debug("Setting AO DCS to Sim")
        ao['AODCSSIM'].write('1')
        ao['AOCOMSIM'].write('1')
        ao['AODCSSFP'].write('0')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        aodcssim_success = ktl.waitfor('($ao.AODCSSIM == enabled)', timeout=3)
        if not aodcssim_success:
            log.error(f'AODCSSIM failed to become enabled')
        aocomsim_success = ktl.waitfor('($ao.AOCOMSIM == enabled)', timeout=3)
        if not aocomsim_success:
            log.error(f'AOCOMSIM failed to become enabled')
        aodcssfp_success = ktl.waitfor('($ao.AODCSSFP == disabled)', timeout=3)
        if not aodcssfp_success:
            log.error(f'AODCSSFP failed to become disabled')
        return aodcssim_success and aocomsim_success and aodcssfp_success
