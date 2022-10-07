

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction


class SetTipTilt(KPFTranslatorFunction):
    '''
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        kpffiu = ktl.cache('kpffiu')
        xdest = args.get('x', None)
        ydest = args.get('y', None)
        if xdest is not None:
            kpffiu['TTXVAX'].write(args.get('x'))
        if ydest is not None:
            kpffiu['TTYVAX'].write(args.get('y'))

    @classmethod
    def post_condition(cls, args, logger, cfg):
        cfg = cls._load_config(cls, cfg)
        timeout = cfg.get('times', 'tip_tilt_move_time', fallback=0.1)
        tol = cfg.get('tolerances', 'tip_tilt_move_tolerance', fallback=0.1)
        xdest = args.get('x', None)
        ydest = args.get('y', None)
        if xdest is not None:
            expr = (f'(kpffiu.TTXVAX > {xdest}-{tol}) and '\
                    f'(kpffiu.TTXVAX < {xdest}+{tol})')
            successx = klt.waitFor(expr, timeout=timeout)
        else:
            successx = True
        if ydest is not None:
            expr = (f'(kpffiu.TTYVAX > {ydest}-{tol}) and '\
                    f'(kpffiu.TTYVAX < {ydest}+{tol})')
            successy = klt.waitFor(expr, timeout=timeout)
        else:
            successy = True
        return successx and successy

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        """
        The arguments to add to the command line interface.
        """
        args_to_add = OrderedDict()
        args_to_add['x'] = {'type': float,
                            'help': 'X position of the tip tilt mirror (TTXVAX)'}
        args_to_add['y'] = {'type': float,
                            'help': 'X position of the tip tilt mirror (TTYVAX)'}

        parser = cls._add_args(parser, args_to_add, print_only=False)
        return super().add_cmdline_args(parser, cfg)
