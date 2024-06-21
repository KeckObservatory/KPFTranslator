import time
import numpy as np
import re

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class FVCPower(KPFTranslatorFunction):
    '''Turn on or off the power for the specified FVC camera.

    Args:
        camera (str): Which FVC camera? Allowed values: SCI, CAHK, EXT, CAL
        power (str): The desired state. Allowed values: on or off

    KTL Keywords Used:

    - `kpfpower.KPFFVC1`
    - `kpfpower.KPFFVC2`
    - `kpfpower.KPFFVC3`
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        check_input(args, 'camera', allowed_values=['SCI', 'CAHK', 'CAL'])

    @classmethod
    def perform(cls, args, logger, cfg):
        camera = args.get('camera')
        camnum = {'SCI': 1, 'CAHK': 2, 'CAL': 3}[camera]
        powerkw = ktl.cache('kpfpower', f'KPFFVC{camnum}')
        dest = args.get('power')
        if powerkw.read().lower() != dest.lower():
            log.info(f"Turning {dest} {camera} FVC")
            powerkw.write(args.get('power'))
            shim = cfg.getfloat('times', 'fvc_command_timeshim', fallback=2)
            time.sleep(shim)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        camera = args.get('camera')
        camnum = {'SCI': 1, 'CAHK': 2, 'CAL': 3}[camera]
        powerkw = ktl.cache('kpfpower', f'KPFFVC{camnum}')
        timeout = cfg.getfloat('times', 'fvc_command_timeout', fallback=1)
        dest = args.get('power')
        success = powerkw.waitFor(f"== '{dest}'", timeout=timeout)
        if success is False:
            raise FailedToReachDestination(powerkw.read(), dest)

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        parser.add_argument('camera', type=str,
                            choices=['SCI', 'CAHK', 'CAL'],
                            help='The FVC camera')
        parser.add_argument('power', type=str,
                            choices=['on', 'off'],
                            help='Desired power state: "on" or "off"')
        return super().add_cmdline_args(parser, cfg)
