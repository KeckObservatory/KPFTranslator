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
        modes = {'green': '', 'red': ''}
        for side in modes.keys():
            normal_file = cfg.get('acf_files', f'{side}_normal')
            fast_file = cfg.get('acf_files', f'{side}_fast')
            ACFFILE = ktl.cache(f'kpf{side}', 'ACFFILE')
            ACFFILE.monitor()
            filename = Path(ACFFILE.ascii).stem
            if filename == normal_file:
                modes[side] = 'normal'
            elif filename == fast_file:
                modes[side] = 'fast'
            else:
                green_mode = 'unknown'

        log.debug(f"Green read mode: {modes['green']}, Red read mode: {modes['red']}")
        print(f"Green read mode: {modes['green']}")
        print(f"Red read mode: {modes['red']}")
        return modes['green'], modes['red']

    @classmethod
    def post_condition(cls, args):
        pass
