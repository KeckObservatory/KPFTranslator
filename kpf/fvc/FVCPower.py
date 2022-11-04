import numpy as np
import re

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import log


class FVCPower(KPFTranslatorFunction):
    '''
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        camera = args.get('camera')
        if camera not in ['SCI', 'CAHK', 'CAL']:
            return False
        camnum = {'SCI': 1, 'CAHK': 2, 'CAL': 3}[camera]

        kpfpower = ktl.cache('kpfpower')
        outlet = kpfpower[f"KPFFVC{camnum}_OUTLETS"].read().strip('kpfpower.')
        outletname = kpfpower[f"{outlet}_NAME"].read()
        if re.search(f"fvc{camnum}", outletname) is None:
            msg = f"Outlet name error: expected 'fvc{camnum}' in '{outletname}'"
            log.error(msg)
            raise Exception(msg)
            return False
        
        locked = kpfpower[f"{outlet}_LOCK"].read() == 'Locked'

        return locked is False

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

    @classmethod
    def post_condition(cls, args, logger, cfg):
        camera = args.get('camera')
        kpfpower = ktl.cache('kpfpower')
        outlet = kpfpower[f"KPFFVC{camnum}_OUTLETS"].read().strip('kpfpower.')
        pwr = args.get('power')
        timeout = cfg.get('times', 'lamp_response_time', fallback=1)
        success = ktl.waitFor(f"($kpfpower.{outlet} == {pwr})", timeout=timeout)
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
