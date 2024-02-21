from pathlib import Path

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class SetFVCExpTime(KPFTranslatorFunction):
    '''Set the exposure time of the specified fiber viewing camera

    ARGS:
    =====
    :camera: Which FVC camera (SCI, CAHK, EXT, CAL)?
    :exptime: The exposure time in seconds.
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        check_input(args, 'camera', allowed_values=['SCI', 'CAHK', 'CAL', 'EXT'])
        check_input(args, 'exptime', value_min=0.005, value_max=60)
        # Check if power is on
        camera = args.get('camera')
        camnum = {'SCI': 1, 'CAHK': 2, 'CAL': 3, 'EXT': None}[camera]
        if camnum is not None:
            powerkw = ktl.cache('kpfpower', f"KPFFVC{camnum}")
            if powerkw.read() != 'On':
                raise FailedPreCondition(f"{camera}FVC power is not On")

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
        timeout = cfg.getfloat('times', 'fvc_command_timeout', fallback=5)
        tol = cfg.getfloat('tolerances', 'guider_exptime_tolerance', fallback=0.01)
        expr = (f'($kpffvc.{camera}EXPTIME > {exptime}-{tol}) '\
                f'and ($kpffvc.{camera}EXPTIME < {exptime}+{tol})')
        success = ktl.waitfor(expr, timeout=timeout)
        if success is not True:
            exptimekw = ktl.cache('kpffvc', f"{camera}EXPTIME")
            raise FailedToReachDestination(exptimekw.read(), exptime)

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        parser.add_argument('camera', type=str,
                            choices=['SCI', 'CAHK', 'CAL', 'EXT'],
                            help='The FVC camera')
        parser.add_argument('exptime', type=float,
                            help='The exposure time in seconds')
        return super().add_cmdline_args(parser, cfg)
