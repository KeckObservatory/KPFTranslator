import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


class SetND1(KPFFunction):
    '''Set the filter in the ND1 filter wheel (the one at the output of the 
    octagon) via the `kpfcal.ND1POS` keyword.

    Args:
        CalND1 (str): The neutral density filter to put in the first filter
            wheel. This affects both the simultaneous calibration light and
            light which can be routed through the FIU to the science and sky
            fibers. Allowed Values: `OD 0.1`, `OD 1.0`, `OD 1.3`, `OD 2.0`,
            `OD 3.0`, `OD 4.0`
        wait (bool): Wait for move to complete before returning? default: True

    KTL Keywords Used:

    - `kpfcal.ND1POS`
    '''
    @classmethod
    def pre_condition(cls, args):
        keyword = ktl.cache('kpfcal', 'ND1POS')
        allowed_values = list(keyword._getEnumerators())
        if 'Unknown' in allowed_values:
            allowed_values.pop(allowed_values.index('Unknown'))
        check_input(args, 'CalND1', allowed_values=allowed_values)

    @classmethod
    def perform(cls, args):
        target = args.get('CalND1')
        log.debug(f"Setting ND1POS to {target}")
        ND1POS = ktl.cache('kpfcal', 'ND1POS')
        ND1POS.write(target, wait=args.get('wait', True))

    @classmethod
    def post_condition(cls, args):
        timeout = cfg.getfloat('times', 'nd_move_time', fallback=20)
        ND1target = args.get('CalND1')
        ND1POS = ktl.cache('kpfcal', 'ND1POS')
        if ND1POS.waitFor(f"== '{ND1target}'", timeout=timeout) == False:
            raise FailedToReachDestination(ND1POS.read(), ND1target)

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('CalND1', type=str,
                            choices=["OD 0.1", "OD 1.0", "OD 1.3", "OD 2.0",
                                     "OD 3.0", "OD 4.0"],
                            help='ND1 Filter to use.')
        parser.add_argument("--nowait", dest="wait",
                            default=True, action="store_false",
                            help="Send move and return immediately?")
        return super().add_cmdline_args(parser)

