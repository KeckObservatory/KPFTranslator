import time
import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


class SetTipTiltPosition(KPFFunction):
    '''Set the position of the tip tilt mirror.

    This should only be used in an engineering context. To control the position
    of a star, set the CURRENT_BASE or PIX_TARGET keywords as appropriate, e.g.
    via the `kpf.fiu.SetTipTiltTargetPixel` translator module function.

    Args:
        x (float): The desired X position (TTXVAX).
        y (float): The desired Y position (TTYVAX).

    KTL Keywords Used:

    - `kpffiu.TTXVAX`
    - `kpffiu.TTYVAX`
    '''
    @classmethod
    def pre_condition(cls, args):
        check_input(args, 'x')
        check_input(args, 'y')

    @classmethod
    def perform(cls, args):
        kpffiu = ktl.cache('kpffiu')
        kpffiu['TTXVAX'].write(args.get('x'))
        kpffiu['TTYVAX'].write(args.get('y'))
        time_shim = cfg.getfloat('times', 'tip_tilt_move_time', fallback=0.1)
        time.sleep(time_shim)

    @classmethod
    def post_condition(cls, args):
        kpffiu = ktl.cache('kpffiu')
        timeout = cfg.getfloat('times', 'tip_tilt_move_time', fallback=0.1)
        tol = cfg.getfloat('tolerances', 'tip_tilt_move_tolerance', fallback=0.1)
        xdest = args.get('x')
        ydest = args.get('y')
        expr = (f'($kpffiu.TTXVAX > {xdest-tol}) and '\
                f'($kpffiu.TTXVAX < {xdest+tol})')
        successx = ktl.waitFor(expr, timeout=timeout)
        if successx is not True:
            raise FailedToReachDestination(kpffiu['TTXVAX'].read(), xdest)
        expr = (f'($kpffiu.TTYVAX > {ydest-tol}) and '\
                f'($kpffiu.TTYVAX < {ydest+tol})')
        successy = ktl.waitFor(expr, timeout=timeout)
        if successy is not True:
            raise FailedToReachDestination(kpffiu['TTYVAX'].read(), ydest)

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('x', type=float,
                            help="X position of the tip tilt mirror (TTXVAX)")
        parser.add_argument('y', type=float,
                            help="X position of the tip tilt mirror (TTYVAX)")
        return super().add_cmdline_args(parser)
