import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction


class TurnHepaOff(KPFTranslatorFunction):
    """
    """

    @classmethod
    def pre_condition(args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        ao = ktl.cache('ao')
        ao['OBHPASTA'].write('0')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        ao = ktl.cache('ao')
        return ktl.waitfor('($ao.OBHPASTA == off)', timeout=3)
