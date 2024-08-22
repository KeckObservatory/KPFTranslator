from pathlib import Path
import time
import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.spectrograph.QueryReadMode import QueryReadMode


class QueryFastReadMode(KPFTranslatorFunction):
    '''Returns True if both ACF files are consistent with fast read mode.
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def perform(cls, args, logger, cfg):
        green_mode, red_mode = QueryReadMode.execute({})
        return (green_mode == 'fast') and (red_mode == 'fast')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass
