import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


class SetTipTiltGain(KPFFunction):
    '''Set the guide loop gain.

    Args:
        GuideLoopGain (float): The desired gain value.

    KTL Keywords Used:

    - `kpfguide.TIPTILT_GAIN`
    '''
    @classmethod
    def pre_condition(cls, args):
        check_input(args, 'GuideLoopGain', value_min=0, value_max=1)

    @classmethod
    def perform(cls, args):
        gain = float(args.get('GuideLoopGain'))
        TIPTILT_GAIN = ktl.cache('kpfguide', 'TIPTILT_GAIN')
        TIPTILT_GAIN.write(gain)

    @classmethod
    def post_condition(cls, args):
        gain = float(args.get('GuideLoopGain'))
        timeout = cfg.getfloat('times', 'tip_tilt_move_time', fallback=0.1)
        tol = cfg.getfloat('tolerances', 'tip_tilt_gain_tolerance', fallback=0.001)
        expr = (f"($kpfguide.TIPTILT_GAIN >= {gain-tol}) and "
                f"($kpfguide.TIPTILT_GAIN <= {gain+tol})")
        success = ktl.waitFor(expr, timeout=timeout)
        if success is not True:
            TIPTILT_GAIN = ktl.cache('kpfguide', 'TIPTILT_GAIN')
            raise FailedToReachDestination(TIPTILT_GAIN.read(), gain)

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('GuideLoopGain', type=float,
                            help="Tip tilt control loop gain")
        return super().add_cmdline_args(parser)
