import time
import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class SetTipTiltPosition(KPFTranslatorFunction):
    '''Set the position of the tip tilt mirror.
    
    This should only be used in an engineering context. To control the position
    of a star, set the CURRENT_BASE or PIX_TARGET keywords as appropriate, e.g.
    via the :py:func:`SetTipTiltTargetPixel` translator module function.
    
    ARGS:
    =====
    :x: The desired X position (TTXVAX).
    :y: The desired Y position (TTYVAX).
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        check_input(args, 'x')
        check_input(args, 'y')
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        kpffiu = ktl.cache('kpffiu')
        kpffiu['TTXVAX'].write(args.get('x'))
        kpffiu['TTYVAX'].write(args.get('y'))
        time_shim = cfg.getfloat('times', 'tip_tilt_move_time', fallback=0.1)
        time.sleep(time_shim)

    @classmethod
    def post_condition(cls, args, logger, cfg):
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
        return successx and successy

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        from collections import OrderedDict
        args_to_add = OrderedDict()
        args_to_add['x'] = {'type': float,
                            'help': 'X position of the tip tilt mirror (TTXVAX)'}
        args_to_add['y'] = {'type': float,
                            'help': 'X position of the tip tilt mirror (TTYVAX)'}

        parser = cls._add_args(parser, args_to_add, print_only=False)
        return super().add_cmdline_args(parser, cfg)
