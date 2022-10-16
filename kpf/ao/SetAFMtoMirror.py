import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction


class SetAFMtoMirror(KPFTranslatorFunction):
    '''Set AFM to Mirror so ACAM sees light
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        ao = ktl.cache('ao')
        ao['OBAMNAME'].write('Mirror')
        ao['OBAMSLEW'].write('1')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        condition = '($ao.OBAMSTST == INPOS) and ($ao.OBAMNAME == Mirror)'
        aoamstst_success = ktl.waitfor(condition, timeout=60)
        if not aoamstst_success:
            print(f'Failed to set AFM to Mirror')
        return aoamstst_success