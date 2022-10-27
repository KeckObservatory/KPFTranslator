

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction


class StartTipTiltCalculations(KPFTranslatorFunction):
    '''
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        success1 = ktl.waitFor('($kpfguide.CONTINUOUS == Active)', timeout=0.01)
        return success1

    @classmethod
    def perform(cls, args, logger, cfg):
        tiptilt = ktl.cache('kpfguide', 'TIPTILT')
        tiptilt.write('Active')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        success1 = ktl.waitFor('($kpfguide.TIPTILT == Active)', timeout=0.01)
        return success1
