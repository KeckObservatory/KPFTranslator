from pathlib import Path

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.guider import guider_is_active, guider_is_saving


class StartGuiderContinuous(KPFTranslatorFunction):
    '''Put the guider in to continuous exposure mode and set images to be saved.
    
    ARGS:
    =====
    None
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
        return guider_is_active() and guider_is_saving()
