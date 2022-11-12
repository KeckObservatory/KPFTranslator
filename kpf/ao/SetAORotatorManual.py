import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import log


class SetAORotatorManual(KPFTranslatorFunction):
    '''AO rotator needs to be in the Manual mode before observing.
    
    ARGS
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        ao = ktl.cache('ao')
        log.debug("Setting AO rotator to manual mode")
        ao['OBRTDSRC'].write('0')
        ao['OBRTMOVE'].write('1')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return ktl.waitfor('($ao.OBRTDSRC == manual)', timeout=3)
