from pathlib import Path

import ktl

from .. import KPFTranslatorFunction


class GuiderLastfile(KPFTranslatorFunction):
    '''
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
