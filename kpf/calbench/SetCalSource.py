from collections import OrderedDict
import numpy as np

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import log


class SetCalSource(KPFTranslatorFunction):
    '''
    Selects which source is fed from the octagon in to the cal bench via the
    kpfcal.OCTAGON keyword.
    
    Valid names: Home, EtalonFiber, BrdbandFiber, U_gold, U_daily,
    Th_daily, Th_gold, SoCal-CalFib, LFCFiber
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        target = args.get('CalSource', None)
        if target is None:
            return False
        allowed_values = ['Home', 'EtalonFiber', 'BrdbandFiber', 'U_gold',
                          'U_daily', 'Th_daily', 'Th_gold', 'SoCal-CalFib',
                          'LFCFiber']
        return target in allowed_values

    @classmethod
    def perform(cls, args, logger, cfg):
        target = args.get('CalSource')
        kpfcal = ktl.cache('kpfcal')
        log.debug(f"  Setting Cal Source (Octagon) to {target}")
        kpfcal['OCTAGON'].write(target)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        '''Verifies that the final OCTAGON keyword value matches the input.
        '''
        target = args.get('CalSource')
        cfg = cls._load_config(cls, cfg)
        timeout = cfg.get('times', 'octagon_move_time', fallback=60)
        expr = f"($kpfcal.OCTAGON == {target})"
        success = ktl.waitFor(expr, timeout=timeout)
        return success

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        args_to_add = OrderedDict()
        args_to_add['CalSource'] = {'type': str,
                                    'help': 'Octagon position to choose?'}
        parser = cls._add_args(parser, args_to_add, print_only=False)
        return super().add_cmdline_args(parser, cfg)

