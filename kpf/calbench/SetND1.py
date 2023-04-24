import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class SetND1(KPFTranslatorFunction):
    '''Set the filter in the ND1 filter wheel (the one at the output of the 
    octagon) via the `kpfcal.ND1POS` keyword.
    
    ARGS:
    =====
    :CalND1: The neutral density filter to put in the first filter wheel.
        Allowed values are "OD 0.1", "OD 1.0", "OD 1.3", "OD 2.0", "OD 3.0",
        "OD 4.0"
    :wait: (bool) Wait for move to complete before returning? (default: True)
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        keyword = ktl.cache('kpfcal', 'ND1POS')
        allowed_values = list(keyword._getEnumerators())
        if 'Unknown' in allowed_values:
            allowed_values.pop(allowed_values.index('Unknown'))
        check_input(args, 'CalND1', allowed_values=allowed_values)

    @classmethod
    def perform(cls, args, logger, cfg):
        target = args.get('CalND1')
        log.debug(f"Setting ND1POS to {target}")
        kpfcal = ktl.cache('kpfcal')
        kpfcal['ND1POS'].write(target, wait=args.get('wait', True))

    @classmethod
    def post_condition(cls, args, logger, cfg):
        timeout = cfg.getfloat('times', 'nd_move_time', fallback=20)
        ND1target = args.get('CalND1')
        ND1POS = ktl.cache('kpfcal', 'ND1POS')
        if ND1POS.waitFor(f"== '{ND1target}'", timeout=timeout) == False:
            raise FailedToReachDestination(ND1POS.read(), ND1target)

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        parser.add_argument('CalND1', type=str,
                            choices=["OD 0.1", "OD 1.0", "OD 1.3", "OD 2.0",
                                     "OD 3.0", "OD 4.0"],
                            help='ND1 Filter to use.')
        parser.add_argument("--nowait", dest="wait",
                            default=True, action="store_false",
                            help="Send move and return immediately?")
        return super().add_cmdline_args(parser, cfg)

