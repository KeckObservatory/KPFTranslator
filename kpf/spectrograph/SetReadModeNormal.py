import time
import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.spectrograph.QueryFastReadMode import QueryFastReadMode


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
        kpfgreen = ktl.cache('kpfgreen')
        kpfred = ktl.cache('kpfred')
        green_normal_file = cfg.get('acf_files', 'green_normal')
        red_normal_file = cfg.get('acf_files', 'red_normal')
        if kpfgreen['ACF'].read() != green_normal_file:
            kpfgreen['ACF'].write(green_normal_file)
        if kpfred['ACF'].read() != red_normal_file:
            kpfred['ACF'].write(red_normal_file)
        time.sleep(2)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        if QueryFastReadMode.execute({}) != False:
            raise FailedPostCondition(f"Read mode change failed")
