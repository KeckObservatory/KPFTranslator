import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class SetTipTiltCalculations(KPFTranslatorFunction):
    '''Turn the tip tilt calculation software on or off.
    
    ARGS:
    =====
    :calculations: The desired state of the calculations (Active or Inactive)
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        allowed_values = ['Active', 'Inactive', '1', '0', 1, 0]
        check_input(args, 'calculations', allowed_values=allowed_values)

    @classmethod
    def perform(cls, args, logger, cfg):
        calculations = args.get('calculations')
        tiptiltcalc = ktl.cache('kpfguide', 'TIPTILT_CALC')
        tiptiltcalc.write(calculations)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        calculations = args.get('calculations')
        timeout = cfg.getfloat('times', 'tip_tilt_move_time', fallback=0.1)
        expr = f"($kpfguide.TIPTILT_CALC == {calculations}) "
        success = ktl.waitFor(expr, timeout=timeout)
        if success is not True:
            tiptilt = ktl.cache('kpfguide', 'TIPTILT_CALC')
            raise FailedToReachDestination(tiptilt.read(), calculations)

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        parser.add_argument('calculations', type=str,
                            help='Calulations "Active" or "Inactive"')
        return super().add_cmdline_args(parser, cfg)
