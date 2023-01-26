from pathlib import Path

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)
from . import fvc_is_ready


class SetFVCExpTime(KPFTranslatorFunction):
    '''Set the exposure time of the specified fiber viewing camera

    ARGS:
    camera - Which FVC camera (SCI, CAHK, EXT, CAL)?
    exptime - The exposure time in seconds.
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        check_input(args, 'camera', allowed_values=['SCI', 'CAHK', 'CAL', 'EXT'])
        camera = args.get('camera')
        if fvc_is_ready(camera=camera) is not True:
            raise FailedPreCondition(f"Camera {camera} is not ready")
        check_input(args, 'exptime', value_min=0.001, value_max=60)
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        camera = args.get('camera')
        kpffvc = ktl.cache('kpffvc')
        exptime = args.get('exptime')
        log.debug(f"Setting {camera} FVC exposure time to {exptime:.3f} s")
        kpffvc[f'{camera}EXPTIME'].write(exptime)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        camera = args.get('camera')
        exptime = args.get('exptime')
        timeout = cfg.get('times', 'fvc_command_timeout', fallback=5)
        tol = cfg.get('tolerances', 'guider_exptime_tolerance', fallback=0.01)
        expr = (f'($kpffvc.{camera}EXPTIME > {exptime}-{tol}) '\
                f'and ($kpffvc.{camera}EXPTIME < {exptime}+{tol})')
        success = ktl.waitfor(expr, timeout=timeout)
        if success is not True:
            exptimekw = ktl.cache('kpffvc', f"{camera}EXPTIME")
            raise FailedToReachDestination(exptimekw.read(), exptime)
        return True

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        from collections import OrderedDict
        args_to_add = OrderedDict()
        args_to_add['camera'] = {'type': str,
                                 'help': 'The camera to use (SCI, CAHK, CAL).'}
        args_to_add['exptime'] = {'type': float,
                                  'help': 'The exposure time in seconds.'}

        parser = cls._add_args(parser, args_to_add, print_only=False)
        return super().add_cmdline_args(parser, cfg)
