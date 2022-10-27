

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction

from . import StartTipTiltCalculations.StartTipTiltCalculations


class StartTipTiltControl(KPFTranslatorFunction):
    '''
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        success1 = ktl.waitFor('($kpfguide.CONTINUOUS == Active)', timeout=0.01)
        success2 = ktl.waitFor('($kpfguide.TIPTILT == Active)', timeout=0.01)
        return success1

    @classmethod
    def perform(cls, args, logger, cfg):
        StartTipTiltCalculations.execute({})
        tiptilt_control = ktl.cache('kpfguide', 'TIPTILT_CONTROL')
        tiptilt_control.write('Active')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        success1 = ktl.waitFor('($kpfguide.TIPTILT_CONTROL == Active)', timeout=0.01)
        return success1
