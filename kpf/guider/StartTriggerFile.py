import ktl

import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)


class StartTriggerFile(KPFTranslatorFunction):
    '''
    
    ARGS: None
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        kpfguide = ktl.cache('kpfguide')
        cube = kpfguide['TRIGCUBE'].read()
        log.info(f"Start guider trigger file data collection: TRIGCUBE={cube}")
        kpfguide['TRIGGER'].write('Active')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True
