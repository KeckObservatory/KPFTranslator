import time
from pathlib import Path
import subprocess

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.fvc.TakeFVCExposure import TakeFVCExposure
from kpf.fvc.SetFVCExpTime import SetFVCExpTime


class TakeFVCContinuous(KPFTranslatorFunction):
    '''Take exposures with the specified FVC continuously and display to ds9.
    
    ARGS:
    =====
    :camera: Which FVC camera (SCI, CAHK, EXT, CAL)?
    :exptime: The exposure time in seconds.
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        check_input(args, 'camera', allowed_values=['SCI', 'CAHK', 'CAL', 'EXT'])
        # Check if power is on
        camera = args.get('camera')
        camnum = {'SCI': 1, 'CAHK': 2, 'CAL': 3}[camera]
        powerkw = ktl.cache('kpfpower', f"KPFFVC{camnum}")
        if powerkw.read() != 'On':
            raise FailedPreCondition(f"{camera}FVC power is not On")

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
        pass

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        parser.add_argument('camera', type=str,
                            choices=['SCI', 'CAHK', 'CAL', 'EXT'],
                            help='The FVC camera')
        parser.add_argument('exptime', type=float,
                            help='The exposure time in seconds')
        return super().add_cmdline_args(parser, cfg)
