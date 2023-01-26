import ktl

from KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)


class SetND1(KPFTranslatorFunction):
    '''Set the filter in the ND1 filter wheel (the one at the output of the 
    octagon) via the `kpfcal.ND1POS` keyword.
    
    Allowed Values:
    "OD 0.1", "OD 1.0", "OD 1.3", "OD 2.0", "OD 3.0", "OD 4.0"
    
    ARGS:
    CalND1 - The neutral density filter to put in the first filter wheel.
    wait (bool) - Wait for move to complete before returning? (default: True)
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        keyword = ktl.cache('kpfcal', 'ND1POS')
        allowed_values = list(keyword._getEnumerators())
        if 'Unknown' in allowed_values:
            allowed_values.pop(allowed_values.index('Unknown'))
        check_input(args, 'CalND1', allowed_values=allowed_values)
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        target = args.get('CalND1')
        log.debug(f"Setting ND1POS to {target}")
        kpfcal = ktl.cache('kpfcal')
        kpfcal['ND1POS'].write(target, wait=args.get('wait', True))

    @classmethod
    def post_condition(cls, args, logger, cfg):
        target = args.get('CalND1')
        timeout = cfg.get('times', 'nd_move_time', fallback=20)
        expr = f"($kpfcal.ND1POS == '{target}')"
        success = ktl.waitFor(expr, timeout=timeout)
        if success is not True:
            kpfcal = ktl.cache('kpfcal')
            raise FailedToReachDestination(kpfcal['ND1POS'].read(), target)

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        from collections import OrderedDict
        args_to_add = OrderedDict()
        args_to_add['CalND1'] = {'type': str,
                                 'help': 'Filter to use'}
        parser = cls._add_args(parser, args_to_add, print_only=False)

        parser = cls._add_bool_arg(parser, 'wait',
            'Return only after move is finished?', default=True)

        return super().add_cmdline_args(parser, cfg)

