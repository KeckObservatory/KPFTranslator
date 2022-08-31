from pathlib import Path

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction


class GuiderLastfile(KPFTranslatorFunction):
    '''Print the value of the kpfguide.LASTFILE keyword to STDOUT
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        kpfguide = ktl.cache('kpfguide')
        lastfile = kpfguide['LASTFILE'].read()
        print(lastfile)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True
