import time
import numpy as np
import re

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class FVCPower(KPFTranslatorFunction):
    '''Turn on or off the power for the specified FVC camera.
    
    ARGS:
    =====
    :camera: Which FVC camera (SCI, CAHK, EXT, CAL)?
    :power: Desired state: on or off
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        camera = args.get('camera')
        cameras = {'SCI': 1, 'CAHK': 2, 'CAL': 3}
        camnum = cameras[camera]
        if camera not in cameras.keys():
            raise FailedPreCondition(f"Input camera {camera} not in allowed values")
        kpfpower = ktl.cache('kpfpower')
        outlet = kpfpower[f"KPFFVC{camnum}_OUTLETS"].read().strip('kpfpower.')
        outletname = kpfpower[f"{outlet}_NAME"].read()
        if re.search(f"fvc{camnum}", outletname) is None:
            raise FailedPreCondition(f"Outlet name error: expected "
                                     f"'fvc{camnum}' in '{outletname}'")
        locked = kpfpower[f"{outlet}_LOCK"].read() == 'Locked'
        if locked is True:
            raise FailedPreCondition(f"Outlet is locked")

    @classmethod
    def perform(cls, args, logger, cfg):
        camera = args.get('camera')
        camnum = {'SCI': 1, 'CAHK': 2, 'CAL': 3}[camera]
        pwr = args.get('power')
        kpfpower = ktl.cache('kpfpower')
        outlet = kpfpower[f"KPFFVC{camnum}_OUTLETS"].read().strip('kpfpower.')
        outletname = kpfpower[f"{outlet}_NAME"].read()
        log.debug(f"Turning {pwr} {camera} FVC (outlet {outlet}: {outletname})")
        kpfpower[f"KPFFVC{camnum}"].write(pwr)
        shim = cfg.getfloat('times', 'fvc_command_timeshim', fallback=2)
        time.sleep(shim)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        camera = args.get('camera')
        cameras = {'SCI': 1, 'CAHK': 2, 'CAL': 3}
        camnum = cameras[camera]
        kpfpower = ktl.cache('kpfpower')
        outlet = kpfpower[f"KPFFVC{camnum}_OUTLETS"].read().strip('kpfpower.')
        pwr = args.get('power')
        timeout = cfg.getfloat('times', 'fvc_command_timeout', fallback=1)
        success = ktl.waitFor(f"($kpfpower.{outlet} == {pwr})", timeout=timeout)
        if success is False:
            raise FailedToReachDestination(kpfpower[outlet].read(), pwr)

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        parser.add_argument('camera', type=str,
                            choices=['SCI', 'CAHK', 'CAL', 'EXT'],
                            help='The FVC camera')
        parser.add_argument('power', type=str,
                            choices=['on', 'off'],
                            help='Desired power state: "on" or "off"')
        return super().add_cmdline_args(parser, cfg)
