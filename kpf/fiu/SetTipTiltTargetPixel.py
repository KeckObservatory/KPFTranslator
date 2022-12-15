import time
import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)


class SetTipTiltTargetPixel(KPFTranslatorFunction):
    '''Set the target pixel of the tip tilt mirror.
    
    ARGS:
    x - The desired X target pixel
    y - The desired Y target pixel
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        min_x_pixel = cfg.get('guider', 'min_x_pixel', fallback=0)
        max_x_pixel = cfg.get('guider', 'max_x_pixel', fallback=640)
        min_y_pixel = cfg.get('guider', 'min_y_pixel', fallback=0)
        max_y_pixel = cfg.get('guider', 'max_y_pixel', fallback=512)
        check_input(args, 'x', value_min=min_x_pixel, value_max=max_x_pixel)
        check_input(args, 'y', value_min=min_y_pixel, value_max=max_y_pixel)
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        x = args.get('x')
        y = args.get('y')
        pixtarget = ktl.cache('kpfguide', 'PIX_TARGET')
        pixtarget.write((x, y))
        time_shim = cfg.get('times', 'tip_tilt_move_time', fallback=0.01)
        time.sleep(time_shim)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        from collections import OrderedDict
        args_to_add = OrderedDict()
        args_to_add['x'] = {'type': float,
                            'help': 'X pixel target'}
        args_to_add['y'] = {'type': float,
                            'help': 'Y pixel target'}

        parser = cls._add_args(parser, args_to_add, print_only=False)
        return super().add_cmdline_args(parser, cfg)
