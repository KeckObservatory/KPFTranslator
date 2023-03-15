import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)


class SetTipTiltCalculations(KPFTranslatorFunction):
    '''Turn the tip tilt control software on or off.
    
    ARGS:
    =====
    :control: The desired state of the calculations (Active or Inactive)
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        allowed_values = ['Active', 'Inactive', '1', '0', 1, 0]
        check_input(args, 'control', allowed_values=allowed_values)
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        control = args.get('control')
        tiptiltcontrol = ktl.cache('kpfguide', 'TIPTILT_CONTROL')
        tiptiltcontrol.write(control)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        control = args.get('control')
        timeout = cfg.get('times', 'tip_tilt_move_time', fallback=0.1)
        expr = f"($kpfguide.TIPTILT_CONTROL == {calculations}) "
        success = ktl.waitFor(expr, timeout=timeout)
        if success is not True:
            tiptiltcontrol = ktl.cache('kpfguide', 'TIPTILT_CONTROL')
            raise FailedToReachDestination(tiptiltcontrol.read(), control)
        return success

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        from collections import OrderedDict
        args_to_add = OrderedDict()
        args_to_add['control'] = {'type': str,
                                  'help': 'Control "Active" or "Inactive"'}
        parser = cls._add_args(parser, args_to_add, print_only=False)
        return super().add_cmdline_args(parser, cfg)
