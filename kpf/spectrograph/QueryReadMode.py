from pathlib import Path
import time
import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


class QueryReadMode(KPFFunction):
    '''Returns string describing the read mode.
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
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

        log.debug(f"Green read mode: {green_mode}, Red read mode: {red_mode}")
        print(f"Green read mode: {green_mode}")
        print(f"Red read mode: {red_mode}")
        return green_mode, red_mode

    @classmethod
    def post_condition(cls, args):
        pass
