import ktl
from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction


class CloseAOHatch(KPFTranslatorFunction):
    """Close the AO Hatch
    """
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        ao = ktl.cache('ao')
        ao['aohatchcmd'].write('close')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        ao = ktl.cache('ao')
        return ktl.waitfor('($ao.AOHATCHSTS == closed)', timeout=30)