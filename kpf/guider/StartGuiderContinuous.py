from pathlib import Path

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction

from .. import check_guider_is_active, check_guider_is_saving

class StartGuiderContinuous(KPFTranslatorFunction):
    '''Put the guider in to continuous exposure mode and set images to be saved.
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        kpfguide = ktl.cache('kpfguide')
        kpfguide['CONTINUOUS'].write('active')
        kpfguide['SAVE'].write('active')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return check_guider_is_active() and check_guider_is_saving()