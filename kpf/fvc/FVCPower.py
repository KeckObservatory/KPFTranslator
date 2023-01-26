import time
import numpy as np
import re

import ktl

from KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination)


class FVCPower(KPFTranslatorFunction):
    '''Turn on or off the power for the specified FVC camera.
    
    ARGS:
    camera - Which FVC camera (SCI, CAHK, EXT, CAL)?
    power - Desired state: on or off
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
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        camera = args.get('camera')
        camnum = {'SCI': 1, 'CAHK': 2, 'CAL': 3}[camera]
        pwr = args.get('power')
        kpfpower = ktl.cache('kpfpower')
        outlet = kpfpower[f"KPFFVC{camnum}_OUTLETS"].read().strip('kpfpower.')
        outletname = kpfpower[f"{outlet}_NAME"].read()
        log.info(f"Turning {pwr} {camera} FVC (outlet {outlet}: {outletname})")
        kpfpower[f"KPFFVC{camnum}"].write(pwr)
        time.sleep(1)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        camera = args.get('camera')
        cameras = {'SCI': 1, 'CAHK': 2, 'CAL': 3}
        camnum = cameras[camera]
        kpfpower = ktl.cache('kpfpower')
        outlet = kpfpower[f"KPFFVC{camnum}_OUTLETS"].read().strip('kpfpower.')
        pwr = args.get('power')
        timeout = cfg.get('times', 'lamp_response_time', fallback=1)
        success = ktl.waitFor(f"($kpfpower.{outlet} == {pwr})", timeout=timeout)
        if success is False:
            raise FailedToReachDestination(kpfpower[outlet].read(), pwr)
        return success

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        from collections import OrderedDict
        args_to_add = OrderedDict()
        args_to_add['camera'] = {'type': str,
                                 'help': 'The camera to use (SCI, CAHK, CAL).'}
        args_to_add['power'] = {'type': str,
                                'help': 'Desired power state: "on" or "off"'}
        parser = cls._add_args(parser, args_to_add, print_only=False)
        return super().add_cmdline_args(parser, cfg)
