import time
import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class DetermineReadMode(KPFTranslatorFunction):
    '''
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def perform(cls, args, logger, cfg):
        kpfgreen = ktl.cache('kpfgreen')
        kpfred = ktl.cache('kpfred')
        green_ACF = kpfgreen['ACF'].read()
        red_ACF = kpfred['ACF'].read()
        log.debug(f"Green ACF File: {green_ACF}")
        log.debug(f"Red ACF File: {red_ACF}")

        green_normal_file = cfg.get('acf_files', 'green_normal')
        green_fast_file = cfg.get('acf_files', 'green_fast')
        red_normal_file = cfg.get('acf_files', 'red_normal')
        red_fast_file = cfg.get('acf_files', 'red_fast')

        if (green_ACF == green_normal_file) and (red_ACF == red_normal_file):
            mode = 'normal'
        elif (green_ACF == green_fast_file) and (red_ACF == red_fast_file):
            mode = 'fast'
        else:
            mode = 'unknown'

        log.info(f"Read mode is {mode}")
        return mode

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass
