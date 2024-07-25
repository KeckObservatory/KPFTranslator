import time
import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.spectrograph.QueryFastReadMode import QueryReadMode


class SetReadModeFast(KPFTranslatorFunction):
    '''Configure both detectors to fast read mode by changing the ACF files
    they are using.

    ARGS:
    =====
    None
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def perform(cls, args, logger, cfg):
        green_mode, red_mode = QueryReadMode.execute({})
        if green_mode != 'fast':
            kpfgreen = ktl.cache('kpfgreen')
            green_fast_file = cfg.get('acf_files', 'green_fast')
            green_ACFFILE = Path(kpfgreen['ACFFILE'].read()).stem
            if green_ACFFILE != green_fast_file:
                kpfgreen['ACF'].write(green_fast_file)
            time.sleep(1)
        if red_mode != 'fast':
            kpfred = ktl.cache('kpfred')
            red_fast_file = cfg.get('acf_files', 'red_fast')
            red_ACFFILE = Path(kpfred['ACFFILE'].read()).stem
            if red_ACFFILE != red_fast_file:
                kpfred['ACF'].write(red_fast_file)
            time.sleep(1)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        green_mode, red_mode = QueryReadMode.execute({})
        if green_mode != 'fast' or red_mode != 'fast':
            raise FailedPostCondition(f"Read mode change failed")
