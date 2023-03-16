import time
from pathlib import Path

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class StopTriggerFile(KPFTranslatorFunction):
    '''Stop a "trigger file" from the guide camera.
    
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
        log.info(f"Stopping guider trigger file data collection")
        kpfguide['TRIGGER'].write('Inactive')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True
