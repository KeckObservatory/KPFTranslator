import time
from pathlib import Path
import subprocess

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)
from . import fvc_is_ready
from .TakeFVCExposure import TakeFVCExposure
from .SetFVCExpTime import SetFVCExpTime


class TakeFVCContinuous(KPFTranslatorFunction):
    '''Take exposures with the specified FVC continuously and display to ds9.
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        check_input(args, 'camera', allowed_values=['SCI', 'CAHK', 'CAL', 'EXT'])
        camera = args.get('camera')
        if fvc_is_ready(camera=camera) is not True:
            raise FailedPreCondition(f"Camera {camera} is not ready")
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        camera = args.get('camera')
        exptime = args.get('exptime')
        SetFVCExpTime.execute(args)
        while True:
            TakeFVCExposure.execute({'camera': camera, 'display': True})
            time.sleep(0.5)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        from collections import OrderedDict
        args_to_add = OrderedDict()
        args_to_add['camera'] = {'type': str,
                                 'help': 'The camera to use (SCI, CAHK, CAL, EXT).'}
        args_to_add['exptime'] = {'type': float,
                                  'help': 'The exposure time in seconds.'}
        parser = cls._add_args(parser, args_to_add, print_only=False)
        return super().add_cmdline_args(parser, cfg)
