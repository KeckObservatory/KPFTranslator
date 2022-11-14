import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import log


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
        ao['OBHPAON'].write('0')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return ktl.waitfor('($ao.OBHPASTA == off)', timeout=3)
