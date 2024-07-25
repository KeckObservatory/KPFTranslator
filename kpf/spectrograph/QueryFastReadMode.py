from pathlib import Path
import time
import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.spectrograph.QueryReadMode import QueryReadMode


class QueryReadMode(KPFTranslatorFunction):
    '''Returns string describing the read mode.
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def perform(cls, args, logger, cfg):
        kpfgreen = ktl.cache('kpfgreen')
        green_normal_file = cfg.get('acf_files', 'green_normal')
        green_fast_file = cfg.get('acf_files', 'green_fast')
        green_ACFFILE = Path(kpfgreen['ACFFILE'].read()).stem
        if green_ACFFILE == green_normal_file:
            green_mode = 'normal'
        elif green_ACFFILE == green_fast_file:
            green_mode = 'fast'
        else:
            green_mode = 'unknown'

        kpfred = ktl.cache('kpfred')
        red_normal_file = cfg.get('acf_files', 'red_normal')
        red_fast_file = cfg.get('acf_files', 'red_fast')
        red_ACFFILE = Path(kpfred['ACFFILE'].read()).stem
        if red_ACFFILE == red_normal_file:
            red_mode = 'normal'
        elif red_ACFFILE == red_fast_file:
            red_mode = 'fast'
        else:
            red_mode = 'unknown'

        msg = f"Green mode: {green_mode}, Red mode: {red_mode}"
        log.debug(msg)
        print(msg)
        return green_mode, red_mode

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass


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
