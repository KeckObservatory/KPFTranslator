import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction


class TurnHepaOn(KPFTranslatorFunction):
    '''Turn HEPA Filter system on
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        ao = ktl.cache('ao')
        ao['OBHPAON'].write('1')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        ao = ktl.cache('ao')
        return ktl.waitfor('($ao.OBHPASTA == on)', timeout=3)
