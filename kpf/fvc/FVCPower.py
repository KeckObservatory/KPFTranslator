import numpy as np

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import log
from . import get_fvc_outlet


class FVCPower(KPFTranslatorFunction):
    '''
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        camera = args.get('camera')
        outlet = get_fvc_outlet(camera=camera)
        kpfpower = ktl.cache('kpfpower')
        locked = kpfpower[f"{outlet}_LOCK"].read() == 'Locked'
        return locked is False

    @classmethod
    def perform(cls, args, logger, cfg):
        camera = args.get('camera')
        outlet = get_fvc_outlet(camera=camera)
        pwr = args.get('power')
        kpfpower = ktl.cache('kpfpower')
        log.info(f"Turning {pwr} {camera}")
        kpfpower[outlet].write(pwr)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        camera = args.get('camera')
        outlet = get_fvc_outlet(camera=camera)
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
