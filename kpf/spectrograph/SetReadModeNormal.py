import time
import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.spectrograph.QueryFastReadMode import QueryReadMode


class SetReadModeNormal(KPFTranslatorFunction):
    '''Configure both detectors to normal read mode by changing the ACF files
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
        if green_mode != 'normal':
            kpfgreen = ktl.cache('kpfgreen')
            green_normal_file = cfg.get('acf_files', 'green_normal')
            green_ACFFILE = Path(kpfgreen['ACFFILE'].read()).stem
            if green_ACFFILE != green_normal_file:
                kpfgreen['ACF'].write(green_normal_file)
            time.sleep(1)
        if red_mode != 'normal':
            kpfred = ktl.cache('kpfred')
            red_normal_file = cfg.get('acf_files', 'red_normal')
            red_ACFFILE = Path(kpfred['ACFFILE'].read()).stem
            if red_ACFFILE != red_normal_file:
                kpfred['ACF'].write(red_normal_file)
            time.sleep(1)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        green_mode, red_mode = QueryReadMode.execute({})
        if green_mode != 'normal' or red_mode != 'normal':
            raise FailedPostCondition(f"Read mode change failed")
