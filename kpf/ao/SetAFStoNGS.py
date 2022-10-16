import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction


class SetAFStoNGS(KPFTranslatorFunction):
    '''ACAM should be set to NGS focus. LGS focus will not work for KPF.
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        ao = ktl.cache('ao')
        ao['OBASNAME'].write('ngs')
        ao['OBASSLEW'].write('1')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        ao = ktl.cache('ao')
        aoamstst_success = ktl.waitfor('($ao.OBASSTST == INPOS)'\
                           and '($ao.OBASNAME == ngs)', timeout=60)
        if not aoamstst_success:
             print(f'Failed to set AFS to ngs')
        return aoamstst_success   
