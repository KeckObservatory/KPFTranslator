import numpy as np

import ktl

from KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)


class WaitForCalSource(KPFTranslatorFunction):
    '''Wait for the move to a cal source is complete (kpfcal.OCTAGON keyword).
    
    Valid names: Home, EtalonFiber, BrdbandFiber, U_gold, U_daily,
    Th_daily, Th_gold, SoCal-CalFib, LFCFiber
    
    ARGS:
    CalSource - The octagon position that is the destination
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        keyword = ktl.cache('kpfcal', 'OCTAGON')
        allowed_values = list(keyword._getEnumerators())
        if 'Unknown' in allowed_values:
            allowed_values.pop(allowed_values.index('Unknown'))
        check_input(args, 'CalSource', allowed_values=allowed_values)
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        target = args.get('CalSource')
        timeout = cfg.get('times', 'octagon_move_time', fallback=60)
        expr = f"($kpfcal.OCTAGON == {target})"
        success = ktl.waitFor(expr, timeout=timeout)
        if success is False:
            log.error(f"Timed out waiting for octagon")

    @classmethod
    def post_condition(cls, args, logger, cfg):
        '''Verifies that the final OCTAGON keyword value matches the input.
        '''
        target = args.get('CalSource')
        timeout = cfg.get('times', 'octagon_move_time', fallback=60)
        expr = f"($kpfcal.OCTAGON == {target})"
        success = ktl.waitFor(expr, timeout=timeout)
        if success is not True:
            kpfcal = ktl.cache('kpfcal')
            raise FailedToReachDestination(kpfcal['OCTAGON'].read(), target)
        return success

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        from collections import OrderedDict
        args_to_add = OrderedDict()
        args_to_add['CalSource'] = {'type': str,
                                    'help': 'Octagon position to choose?'}
        parser = cls._add_args(parser, args_to_add, print_only=False)
        return super().add_cmdline_args(parser, cfg)

