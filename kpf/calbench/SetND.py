import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)


class SetND(KPFTranslatorFunction):
    '''Set the filter in the ND1 & ND2 filter wheels via the `kpfcal.ND1POS`
    and `kpfcal.ND2POS` keywords.
    
    Allowed Values:
    ND1: "OD 0.1", "OD 1.0", "OD 1.3", "OD 2.0", "OD 3.0", "OD 4.0"
    ND2: "OD 0.1", "OD 0.3", "OD 0.5", "OD 0.8", "OD 1.0", "OD 4.0"
    
    ARGS:
    =====
    :CalND1: The neutral density filter to put in the first filter wheel.
    :CalND2: The neutral density filter to put in the second filter wheel.
    :wait: (bool) Wait for move to complete before returning? (default: True)
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        keyword = ktl.cache('kpfcal', 'ND1POS')
        allowed_values = list(keyword._getEnumerators())
        if 'Unknown' in allowed_values:
            allowed_values.pop(allowed_values.index('Unknown'))
        check_input(args, 'CalND1', allowed_values=allowed_values)
        keyword = ktl.cache('kpfcal', 'ND2POS')
        allowed_values = list(keyword._getEnumerators())
        if 'Unknown' in allowed_values:
            allowed_values.pop(allowed_values.index('Unknown'))
        check_input(args, 'CalND2', allowed_values=allowed_values)
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        kpfcal = ktl.cache('kpfcal')
        ND1target = args.get('CalND1')
        log.debug(f"Setting ND1POS to {ND1target}")
        kpfcal['ND1POS'].write(ND1target, wait=args.get('wait', True))
        ND2target = args.get('CalND2')
        log.debug(f"Setting ND2POS to {ND2target}")
        kpfcal['ND2POS'].write(ND2target, wait=args.get('wait', True))

    @classmethod
    def post_condition(cls, args, logger, cfg):
        ND1target = args.get('CalND1')
        ND2target = args.get('CalND2')
        timeout = cfg.get('times', 'nd_move_time', fallback=20)
        ND1expr = f"($kpfcal.ND1POS == '{ND1target}')"
        ND1success = ktl.waitFor(ND1expr, timeout=timeout)
        ND2expr = f"($kpfcal.ND2POS == '{ND2target}')"
        ND2success = ktl.waitFor(ND2expr, timeout=timeout)
        if ND1success is not True:
            kpfcal = ktl.cache('kpfcal')
            raise FailedToReachDestination(kpfcal['ND1POS'].read(), ND1target)
        if ND2success is not True:
            kpfcal = ktl.cache('kpfcal')
            raise FailedToReachDestination(kpfcal['ND2POS'].read(), ND2target)

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        from collections import OrderedDict
        args_to_add = OrderedDict()
        args_to_add['CalND1'] = {'type': str,
                                 'help': 'ND1 Filter to use'}
        args_to_add['CalND2'] = {'type': str,
                                 'help': 'ND2 Filter to use'}
        parser = cls._add_args(parser, args_to_add, print_only=False)

        parser = cls._add_bool_arg(parser, 'wait',
            'Return only after move is finished?', default=True)

        return super().add_cmdline_args(parser, cfg)

