import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class SetND2(KPFTranslatorFunction):
    '''Set the filter in the ND2 filter wheel (the one at the output of the 
    octagon) via the `kpfcal.ND2POS` keyword.
    
    ARGS:
    =====
    :CalND2: The neutral density filter to put in the second filter wheel.
        Allowed values are "OD 0.1", "OD 0.3", "OD 0.5", "OD 0.8", "OD 1.0",
        "OD 4.0"
    :wait: (bool) Wait for move to complete before returning? (default: True)
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        keyword = ktl.cache('kpfcal', 'ND2POS')
        allowed_values = list(keyword._getEnumerators())
        if 'Unknown' in allowed_values:
            allowed_values.pop(allowed_values.index('Unknown'))
        check_input(args, 'CalND2', allowed_values=allowed_values)
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        target = args.get('CalND2')
        log.debug(f"Setting ND2POS to {target}")
        kpfcal = ktl.cache('kpfcal')
        kpfcal['ND2POS'].write(target, wait=args.get('wait', True))

    @classmethod
    def post_condition(cls, args, logger, cfg):
        target = args.get('CalND2')
        timeout = cfg.get('times', 'nd_move_time', fallback=20)
        expr = f"($kpfcal.ND2POS == '{target}')"
        success = ktl.waitFor(expr, timeout=timeout)
        if success is not True:
            kpfcal = ktl.cache('kpfcal')
            raise FailedToReachDestination(kpfcal['ND2POS'].read(), target)

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        from collections import OrderedDict
        args_to_add = OrderedDict()
        args_to_add['CalND2'] = {'type': str,
                                 'help': 'Filter to use'}
        parser = cls._add_args(parser, args_to_add, print_only=False)

        parser = cls._add_bool_arg(parser, 'wait',
            'Return only after move is finished?', default=True)

        return super().add_cmdline_args(parser, cfg)
