import numpy as np

import ktl

from kpf import log, cfg, check_input
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


class WaitForCalSource(KPFFunction):
    '''Wait for the move to a cal source is complete (kpfcal.OCTAGON keyword).

    Args:
        CalSource (str): Which lamp to select? Allowed Values: EtalonFiber,
            BrdbandFiber, U_gold, U_daily, Th_daily, Th_gold, SoCal-CalFib,
            LFCFiber

    KTL Keywords Used:

    - `kpfcal.OCTAGON`
    '''
    @classmethod
    def pre_condition(cls, args):
        keyword = ktl.cache('kpfcal', 'OCTAGON')
        allowed_values = list(keyword._getEnumerators())
        if 'Unknown' in allowed_values:
            allowed_values.pop(allowed_values.index('Unknown'))
        check_input(args, 'CalSource', allowed_values=allowed_values)

    @classmethod
    def perform(cls, args):
        target = args.get('CalSource')
        timeout = cfg.getfloat('times', 'octagon_move_time', fallback=60)
        expr = f"($kpfcal.OCTAGON == {target})"
        success = ktl.waitFor(expr, timeout=timeout)
        if success is False:
            log.error(f"Timed out waiting for octagon")

    @classmethod
    def post_condition(cls, args):
        target = args.get('CalSource')
        timeout = cfg.getfloat('times', 'octagon_move_time', fallback=60)
        expr = f"($kpfcal.OCTAGON == {target})"
        success = ktl.waitFor(expr, timeout=timeout)
        if success is not True:
            kpfcal = ktl.cache('kpfcal')
            raise FailedToReachDestination(kpfcal['OCTAGON'].read(), target)

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('CalSource', type=str,
                            choices=['Home', 'EtalonFiber', 'BrdbandFiber',
                                     'U_gold', 'U_daily', 'Th_daily', 'Th_gold',
                                     'SoCal-CalFib', 'LFCFiber'],
                            help='Octagon position to choose?')
        return super().add_cmdline_args(parser)

