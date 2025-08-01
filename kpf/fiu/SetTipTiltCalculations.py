import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


class SetTipTiltCalculations(KPFFunction):
    '''Turn the tip tilt calculation software on or off.

    Args:
        calculations (str): The desired state of the calculations. Allowed
            values: Active or Inactive

    KTL Keywords Used:

    - `kpfguide.TIPTILT_CALC`
    '''
    @classmethod
    def pre_condition(cls, args):
        allowed_values = ['Active', 'Inactive', '1', '0', 1, 0]
        check_input(args, 'calculations', allowed_values=allowed_values)

    @classmethod
    def perform(cls, args):
        calculations = args.get('calculations')
        TIPTILT_CALC = ktl.cache('kpfguide', 'TIPTILT_CALC')
        TIPTILT_CALC.write(calculations)

    @classmethod
    def post_condition(cls, args):
        calculations = args.get('calculations')
        timeout = cfg.getfloat('times', 'tip_tilt_move_time', fallback=0.1)
        expr = f"($kpfguide.TIPTILT_CALC == {calculations}) "
        success = ktl.waitFor(expr, timeout=timeout)
        if success is not True:
            TIPTILT_CALC = ktl.cache('kpfguide', 'TIPTILT_CALC')
            raise FailedToReachDestination(TIPTILT_CALC.read(), calculations)

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('calculations', type=str,
                            choices=['Active', 'Inactive'],
                            help='Calulations "Active" or "Inactive"')
        return super().add_cmdline_args(parser)
