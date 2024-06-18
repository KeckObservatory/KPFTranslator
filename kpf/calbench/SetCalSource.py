import numpy as np

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class SetCalSource(KPFTranslatorFunction):
    '''Selects which source is fed from the octagon in to the cal bench via the
    `kpfcal.OCTAGON` keyword.

    Args:
        CalSource (str): Which lamp to select? Allowed Values: EtalonFiber,
            BrdbandFiber, U_gold, U_daily, Th_daily, Th_gold, SoCal-CalFib,
            LFCFiber

    KTL Keywords Used:

    - `kpfcal.OCTAGON`
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        keyword = ktl.cache('kpfcal', 'OCTAGON')
        allowed_values = list(keyword._getEnumerators())
        if 'Unknown' in allowed_values:
            allowed_values.pop(allowed_values.index('Unknown'))
        check_input(args, 'CalSource', allowed_values=allowed_values)

    @classmethod
    def perform(cls, args, logger, cfg):
        target = args.get('CalSource')
        kpfcal = ktl.cache('kpfcal')
        log.debug(f"Setting Cal Source (Octagon) to {target}")
        kpfcal['OCTAGON'].write(target, wait=args.get('wait', True))

    @classmethod
    def post_condition(cls, args, logger, cfg):
        target = args.get('CalSource')
        timeout = cfg.getfloat('times', 'octagon_move_time', fallback=90)
        expr = f"($kpfcal.OCTAGON == {target})"
        success = ktl.waitFor(expr, timeout=timeout)
        if success is not True:
            kpfcal = ktl.cache('kpfcal')
            raise FailedToReachDestination(kpfcal['OCTAGON'].read(), target)

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        parser.add_argument('CalSource', type=str,
                            choices=['Home', 'EtalonFiber', 'BrdbandFiber',
                                     'U_gold', 'U_daily', 'Th_daily', 'Th_gold',
                                     'SoCal-CalFib', 'LFCFiber'],
                            help='Octagon position to choose?')
        parser.add_argument("--nowait", dest="wait",
                            default=True, action="store_false",
                            help="Send move and return immediately?")
        return super().add_cmdline_args(parser, cfg)

