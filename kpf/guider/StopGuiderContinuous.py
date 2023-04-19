from pathlib import Path

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.guider import guider_is_active, guider_is_saving


class StopGuiderContinuous(KPFTranslatorFunction):
    '''Stop the guider's continuous exposure mode and stop saving images.
    
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
        kpfguide['CONTINUOUS'].write('inactive')
        kpfguide['SAVE'].write('inactive')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return not guider_is_active() and not guider_is_saving()
