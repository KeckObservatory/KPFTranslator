import numpy as np

import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


class SetCalSource(KPFFunction):
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
    def pre_condition(cls, args):
        keyword = ktl.cache('kpfcal', 'OCTAGON')
        allowed_values = list(keyword._getEnumerators())
        if 'Unknown' in allowed_values:
            allowed_values.pop(allowed_values.index('Unknown'))
        check_input(args, 'CalSource', allowed_values=allowed_values)

    @classmethod
    def perform(cls, args):
        target = args.get('CalSource')
        OCTAGON = ktl.cache('kpfcal', 'OCTAGON')
        log.debug(f"Setting Cal Source (Octagon) to {target}")
        OCTAGON.write(target, wait=args.get('wait', True))

    @classmethod
    def post_condition(cls, args):
        target = args.get('CalSource')
        timeout = cfg.getfloat('times', 'octagon_move_time', fallback=90)
        OCTAGON = ktl.cache('kpfcal', 'OCTAGON')
        if OCTAGON.waitFor(f'== "{target}"', timeout=timeout) is not True:
            raise FailedToReachDestination(OCTAGON.read(), target)

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('CalSource', type=str,
                            choices=['Home', 'EtalonFiber', 'BrdbandFiber',
                                     'U_gold', 'U_daily', 'Th_daily', 'Th_gold',
                                     'SoCal-CalFib', 'LFCFiber'],
                            help='Octagon position to choose?')
        parser.add_argument("--nowait", dest="wait",
                            default=True, action="store_false",
                            help="Send move and return immediately?")
        return super().add_cmdline_args(parser)

