import time
import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.spectrograph.QueryFastReadMode import QueryFastReadMode


class SetReadModeFast(KPFTranslatorFunction):
    '''

    ARGS:
    None
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def perform(cls, args, logger, cfg):
        kpfgreen = ktl.cache('kpfgreen')
        kpfred = ktl.cache('kpfred')
        green_fast_file = cfg.get('acf_files', 'green_fast')
        red_fast_file = cfg.get('acf_files', 'red_fast')
        kpfgreen['ACF'].write(green_fast_file)
        kpfred['ACF'].write(red_fast_file)
        time.sleep(2)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        if QueryFastReadMode.execute({}) != True:
            raise FailedPostCondition(f"Read mode change failed")
