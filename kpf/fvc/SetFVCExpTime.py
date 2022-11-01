from pathlib import Path

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction

from . import fvc_is_ready


class SetFVCExpTime(KPFTranslatorFunction):
    '''Set the exposure time of the specified fiber viewing camera
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        camera = args.get('camera', 'SCI')
        return fvc_is_ready(camera=camera)

    @classmethod
    def perform(cls, args, logger, cfg):
        camera = args.get('camera', 'SCI')
        kpffvc = ktl.cache('kpffvc')
        exptime = args.get('exptime', None)
        if exptime is not None:
            kpffvc[f'{camera}EXPTIME'].write(exptime)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        camera = args.get('camera', 'SCI')
        exptime = args.get('exptime', None)
        if exptime is not None:
            cfg = cls._load_config(cls, cfg)
            timeout = cfg.get('times', 'fvc_command_timeout', fallback=5)
            tol = cfg.get('tolerances', 'guider_exptime_tolerance', fallback=0.01)
            expr = (f'($kpffvc.{camera}EXPTIME > {exptime}-{tol}) '\
                    f'and ($kpffvc.{camera}EXPTIME < {exptime}+{tol})')
            return ktl.waitfor(expr, timeout=timeout)

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
