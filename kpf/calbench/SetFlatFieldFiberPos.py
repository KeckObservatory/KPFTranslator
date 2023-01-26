import ktl

from KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)


class SetFlatFieldFiberPos(KPFTranslatorFunction):
    '''Set the flat field fiber aperture via the `kpfcal.FF_FIBERPOS` keyword.
    
    Allowed Values:
    "Blank", "6 mm f/5", "7.5 mm f/4", "10 mm f/3", "13.2 mm f/2.3", "Open"
    
    ARGS:
    FF_FiberPos - The name of the flat field fiber position desired.
    wait (bool) - Wait for move to complete before returning? (default: True)
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        keyword = ktl.cache('kpfcal', 'FF_FiberPos')
        allowed_values = list(keyword._getEnumerators())
        if 'Unknown' in allowed_values:
            allowed_values.pop(allowed_values.index('Unknown'))
        check_input(args, 'FF_FiberPos', allowed_values=allowed_values)
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        target = args.get('FF_FiberPos')
        log.debug(f"Setting FF_FiberPos to {target}")
        kpfcal = ktl.cache('kpfcal')
        kpfcal['FF_FiberPos'].write(target, wait=args.get('wait', True))

    @classmethod
    def post_condition(cls, args, logger, cfg):
        target = args.get('FF_FiberPos')
        timeout = cfg.get('times', 'nd_move_time', fallback=20)
        expr = f"($kpfcal.FF_FiberPos == '{target}')"
        success = ktl.waitFor(expr, timeout=timeout)
        if success is not True:
            kpfcal = ktl.cache('kpfcal')
            raise FailedToReachDestination(kpfcal['FF_FiberPos'].read(), target)
        return True

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        from collections import OrderedDict
        args_to_add = OrderedDict()
        args_to_add['FF_FiberPos'] = {'type': str,
                                      'help': 'Wide flat aperture to use.'}
        parser = cls._add_args(parser, args_to_add, print_only=False)

        parser = cls._add_bool_arg(parser, 'wait',
            'Return only after move is finished?', default=True)
        return super().add_cmdline_args(parser, cfg)
