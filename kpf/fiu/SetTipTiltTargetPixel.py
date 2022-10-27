from collections import OrderedDict

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction


class SetTipTiltTargetPixel(KPFTranslatorFunction):
    '''
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        x = args.get('x', None)
        y = args.get('y', None)
        if x is None or y is None:
            return False
        cfg = cls._load_config(cls, cfg)
        min_x_pixel = cfg.get('guider', 'min_x_pixel', fallback=0)
        max_x_pixel = cfg.get('guider', 'max_x_pixel', fallback=640)
        min_y_pixel = cfg.get('guider', 'min_y_pixel', fallback=0)
        max_y_pixel = cfg.get('guider', 'max_y_pixel', fallback=512)
        return (x >= min_x_pixel) and (y >= min_y_pixel) and (x <= max_x_pixel) and (y <= max_y_pixel)

    @classmethod
    def perform(cls, args, logger, cfg):
        x = args.get('x')
        y = args.get('y')
        pixtarget = ktl.cache('kpfguide', 'PIX_TARGET')
        pixtarget.write((x, y))

    @classmethod
    def post_condition(cls, args, logger, cfg):
#         x = args.get('x')
#         y = args.get('y')
#         cfg = cls._load_config(cls, cfg)
#         timeout = cfg.get('times', 'tip_tilt_move_time', fallback=0.1)
#         expr = (f"($kpfguide.PIX_TARGET == {}) "
#         success = ktl.waitFor(expr, timeout=timeout)
#         return success
        return True

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        """
        The arguments to add to the command line interface.
        """
        args_to_add = OrderedDict()
        args_to_add['x'] = {'type': float,
                            'help': 'X pixel target'}
        args_to_add['y'] = {'type': float,
                            'help': 'Y pixel target'}

        parser = cls._add_args(parser, args_to_add, print_only=False)
        return super().add_cmdline_args(parser, cfg)
