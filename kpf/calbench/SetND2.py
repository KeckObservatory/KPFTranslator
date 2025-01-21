import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class SetND2(KPFTranslatorFunction):
    '''Set the filter in the ND2 filter wheel (the one at the output of the 
    octagon) via the `kpfcal.ND2POS` keyword.

    Args:
        CalND2 (str): The neutral density filter to put in the second filter
            wheel. This affects only the light injected in to the simultaneous
            calibration fiber. Allowed Values: `OD 0.1`, `OD 0.3`, `OD 0.5`,
            `OD 0.8`, `OD 1.0`, `OD 4.0`
        wait (bool): Wait for move to complete before returning? default: True

    KTL Keywords Used:

    - `kpfcal.ND2POS`
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        keyword = ktl.cache('kpfcal', 'ND2POS')
        allowed_values = list(keyword._getEnumerators())
        if 'Unknown' in allowed_values:
            allowed_values.pop(allowed_values.index('Unknown'))
        check_input(args, 'CalND2', allowed_values=allowed_values)

    @classmethod
    def perform(cls, args, logger, cfg):
        target = args.get('CalND2')
        log.debug(f"Setting ND2POS to {target}")
        kpfcal = ktl.cache('kpfcal')
        kpfcal['ND2POS'].write(target, wait=args.get('wait', True))

    @classmethod
    def post_condition(cls, args, logger, cfg):
        timeout = cfg.getfloat('times', 'nd_move_time', fallback=20)
        ND2target = args.get('CalND2')
        ND2POS = ktl.cache('kpfcal', 'ND2POS')
        if ND2POS.waitFor(f"== '{ND2target}'", timeout=timeout) == False:
            raise FailedToReachDestination(ND2POS.read(), ND2target)

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        parser.add_argument('CalND2', type=str,
                            choices=["OD 0.1", "OD 0.3", "OD 0.5", "OD 0.8",
                                     "OD 1.0", "OD 4.0"],
                            help='ND2 Filter to use.')
        parser.add_argument("--nowait", dest="wait",
                            default=True, action="store_false",
                            help="Send move and return immediately?")
        return super().add_cmdline_args(parser, cfg)
