import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class WaitForND1(KPFTranslatorFunction):
    '''Wait for the ND1 filter wheel (the one at the output of the 
    octagon) via the `kpfcal.ND1POS` keyword.
    
    Allowed Values:
    "OD 0.1", "OD 1.0", "OD 1.3", "OD 2.0", "OD 3.0", "OD 4.0"
    
    ARGS:
    =====
    :CalND1: The neutral density filter to put in the first filter wheel.
        Allowed values are "OD 0.1", "OD 1.0", "OD 1.3", "OD 2.0", "OD 3.0",
        "OD 4.0"
    :CalND2: The neutral density filter to put in the second filter wheel.
        Allowed values are "OD 0.1", "OD 0.3", "OD 0.5", "OD 0.8", "OD 1.0",
        "OD 4.0"
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
        ND1target = args.get('CalND1')
        ND2target = args.get('CalND2')
        timeout = cfg.getfloat('times', 'nd_move_time', fallback=20)
        ND1expr = f"($kpfcal.ND1POS == '{ND1target}')"
        ND1success = ktl.waitFor(ND1expr, timeout=timeout)
        ND2expr = f"($kpfcal.ND2POS == '{ND2target}')"
        ND2success = ktl.waitFor(ND2expr, timeout=timeout)
        if ND1success is not True:
            log.error(f"Timed out waiting for ND1 filter wheel")
        if ND2success is not True:
            log.error(f"Timed out waiting for ND2 filter wheel")

    @classmethod
    def post_condition(cls, args, logger, cfg):
        ND1target = args.get('CalND1')
        ND2target = args.get('CalND2')
        ND1expr = f"($kpfcal.ND1POS == '{ND1target}')"
        ND1success = ktl.waitFor(ND1expr, timeout=timeout)
        ND2expr = f"($kpfcal.ND2POS == '{ND2target}')"
        ND2success = ktl.waitFor(ND2expr, timeout=timeout)
        return ND1success and ND2success

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        from collections import OrderedDict
        args_to_add = OrderedDict()
        args_to_add['CalND1'] = {'type': str,
                                 'help': 'Filter to use'}
        parser = cls._add_args(parser, args_to_add, print_only=False)
        return super().add_cmdline_args(parser, cfg)

