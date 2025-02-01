import time
from pathlib import Path
import subprocess

import ktl

from kpf import log, cfg, check_input
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.fvc.TakeFVCExposure import TakeFVCExposure
from kpf.fvc.SetFVCExpTime import SetFVCExpTime


class TakeFVCContinuous(KPFFunction):
    '''Take exposures with the specified FVC continuously and display to ds9.

    Args:
        camera (str): Which FVC camera? Allowed values: SCI, CAHK, EXT, CAL
        exptime (float): The exposure time in seconds.

    KTL Keywords Used:

    - `kpffvc.SCIEXPTIME`
    - `kpffvc.CAHKEXPTIME`
    - `kpffvc.EXTEXPTIME`
    - `kpffvc.CALEXPTIME`
    - `kpfpower.KPFFVC1`
    - `kpfpower.KPFFVC2`
    - `kpfpower.KPFFVC3`
    '''
    @classmethod
    def pre_condition(cls, args):
        check_input(args, 'camera', allowed_values=['SCI', 'CAHK', 'CAL', 'EXT'])
        # Check if power is on
        camera = args.get('camera')
        camnum = {'SCI': 1, 'CAHK': 2, 'CAL': 3}[camera]
        powerkw = ktl.cache('kpfpower', f"KPFFVC{camnum}")
        if powerkw.read() != 'On':
            raise FailedPreCondition(f"{camera}FVC power is not On")

    @classmethod
    def perform(cls, args):
        camera = args.get('camera')
        exptime = args.get('exptime')
        SetFVCExpTime.execute(args)
        while True:
            TakeFVCExposure.execute({'camera': camera, 'display': True})
            time.sleep(0.5)

    @classmethod
    def post_condition(cls, args):
        pass

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('camera', type=str,
                            choices=['SCI', 'CAHK', 'CAL', 'EXT'],
                            help='The FVC camera')
        parser.add_argument('exptime', type=float,
                            help='The exposure time in seconds')
        return super().add_cmdline_args(parser)
