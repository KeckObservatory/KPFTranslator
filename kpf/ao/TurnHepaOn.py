import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import log


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
        ao['OBHPAON'].write('1')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return ktl.waitfor('($ao.OBHPASTA == on)', timeout=3)
