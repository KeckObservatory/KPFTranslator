import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class SetTipTiltControl(KPFTranslatorFunction):
    '''Turn the tip tilt control software on or off.

    Args:
        control (str): The desired state of the control. Allowed values: Active
            or Inactive

    KTL Keywords Used:

    - `kpfguide.TIPTILT_CONTROL`
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        allowed_values = ['Active', 'Inactive', '1', '0', 1, 0]
        check_input(args, 'control', allowed_values=allowed_values)

    @classmethod
    def perform(cls, args, logger, cfg):
        control = args.get('control')
        tiptiltcontrol = ktl.cache('kpfguide', 'TIPTILT_CONTROL')
        tiptiltcontrol.write(control)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        control = args.get('control')
        timeout = cfg.getfloat('times', 'tip_tilt_move_time', fallback=0.1)
        expr = f"($kpfguide.TIPTILT_CONTROL == {calculations}) "
        success = ktl.waitFor(expr, timeout=timeout)
        if success is not True:
            tiptiltcontrol = ktl.cache('kpfguide', 'TIPTILT_CONTROL')
            raise FailedToReachDestination(tiptiltcontrol.read(), control)

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        parser.add_argument('control', type=str,
                            choices=['Active', 'Inactive'],
                            help='Control "Active" or "Inactive"')
        return super().add_cmdline_args(parser, cfg)
