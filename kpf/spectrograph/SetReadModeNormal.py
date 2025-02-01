import time
import ktl

from kpf import log, cfg, check_input
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.spectrograph.QueryFastReadMode import QueryFastReadMode


class SetReadModeNormal(KPFFunction):
    '''Configure both detectors to normal read mode by changing the ACF files
    they are using.

    ARGS:
    =====
    None
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        kpfgreen = ktl.cache('kpfgreen')
        kpfred = ktl.cache('kpfred')
        green_normal_file = cfg.get('acf_files', 'green_normal')
        red_normal_file = cfg.get('acf_files', 'red_normal')
        kpfgreen['ACF'].write(green_normal_file)
        kpfred['ACF'].write(red_normal_file)
        time.sleep(2)

    @classmethod
    def post_condition(cls, args):
        if QueryFastReadMode.execute({}) != False:
            raise FailedPostCondition(f"Read mode change failed")
