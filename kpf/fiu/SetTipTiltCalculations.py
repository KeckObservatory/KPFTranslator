import ktl

from KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)


class SetTipTiltCalculations(KPFTranslatorFunction):
    '''Turn the tip tilt calculation software on or off.
    
    ARGS:
    calculations - The desired state of the calculations (Active or Inactive)
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        allowed_values = ['Active', 'Inactive', '1', '0', 1, 0]
        check_input(args, 'calculations', allowed_values=allowed_values)
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        calculations = args.get('calculations')
        tiptiltcalc = ktl.cache('kpfguide', 'TIPTILT_CALC')
        tiptiltcalc.write(calculations)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        calculations = args.get('calculations')
        timeout = cfg.get('times', 'tip_tilt_move_time', fallback=0.1)
        expr = f"($kpfguide.TIPTILT_CALC == {calculations}) "
        success = ktl.waitFor(expr, timeout=timeout)
        if success is not True:
            tiptilt = ktl.cache('kpfguide', 'TIPTILT_CALC')
            raise FailedToReachDestination(tiptilt.read(), calculations)
        return success

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        from collections import OrderedDict
        args_to_add = OrderedDict()
        args_to_add['calculations'] = {'type': str,
                                       'help': 'Calulations "Active" or "Inactive"'}
        parser = cls._add_args(parser, args_to_add, print_only=False)
        return super().add_cmdline_args(parser, cfg)
