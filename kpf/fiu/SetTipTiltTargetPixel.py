import time
import ktl

from kpf import log, cfg, check_input
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


class SetTipTiltTargetPixel(KPFFunction):
    '''Set the target pixel of the tip tilt mirror.  This sets the CURRENT_BASE
    keyword.

    Args:
        x (float): The desired X target pixel.
        y (float): The desired Y target pixel.

    KTL Keywords Used:

    - `kpfguide.CURRENT_BASE`
    '''
    @classmethod
    def pre_condition(cls, args):
        min_x_pixel = cfg.getint('guider', 'min_x_pixel', fallback=0)
        max_x_pixel = cfg.getint('guider', 'max_x_pixel', fallback=640)
        min_y_pixel = cfg.getint('guider', 'min_y_pixel', fallback=0)
        max_y_pixel = cfg.getint('guider', 'max_y_pixel', fallback=512)
        check_input(args, 'x', value_min=min_x_pixel, value_max=max_x_pixel)
        check_input(args, 'y', value_min=min_y_pixel, value_max=max_y_pixel)

    @classmethod
    def perform(cls, args):
        x = args.get('x')
        y = args.get('y')
        pixtarget = ktl.cache('kpfguide', 'CURRENT_BASE')
        pixtarget.write((x, y))
        time_shim = cfg.getfloat('times', 'tip_tilt_move_time', fallback=0.01)
        time.sleep(time_shim)

    @classmethod
    def post_condition(cls, args):
        pass

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('x', type=float,
                            help="X pixel target (CURRENT_BASE)")
        parser.add_argument('y', type=float,
                            help="Y pixel target (CURRENT_BASE)")
        return super().add_cmdline_args(parser)
