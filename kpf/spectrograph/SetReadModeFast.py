import time
import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.spectrograph.QueryFastReadMode import QueryFastReadMode


class SetReadModeFast(KPFFunction):
    '''Configure both detectors to fast read mode by changing the ACF files
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
        green_fast_file = cfg.get('acf_files', 'green_fast')
        red_fast_file = cfg.get('acf_files', 'red_fast')
        kpfgreen['ACF'].write(green_fast_file)
        kpfred['ACF'].write(red_fast_file)
        time.sleep(2)

    @classmethod
    def post_condition(cls, args):
        if QueryFastReadMode.execute({}) != True:
            raise FailedPostCondition(f"Read mode change failed")
