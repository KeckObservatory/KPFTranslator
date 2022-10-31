from collections import OrderedDict

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction


class TipTiltPerformanceCheck(KPFTranslatorFunction):
    '''
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True
