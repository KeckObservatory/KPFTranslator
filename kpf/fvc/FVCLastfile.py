from pathlib import Path

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class FVCLastfile(KPFTranslatorFunction):
    '''Print the value of the kpffvc.[camera]LASTFILE keyword to STDOUT

    Args:
        camera (str): Which FVC camera? Allowed values: SCI, CAHK, EXT, CAL

    Returns:
        String containing the path to the file.

    KTL Keywords Used:

    - `kpffvc.SCILASTFILE`
    - `kpffvc.CALLASTFILE`
    - `kpffvc.EXTLASTFILE`
    - `kpffvc.CAHKLASTFILE`
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        check_input(args, 'camera', allowed_values=['SCI', 'CAHK', 'CAL', 'EXT'])

    @classmethod
    def perform(cls, args, logger, cfg):
        camera = args.get('camera')
        kpffvc = ktl.cache('kpffvc')
        lastfile = kpffvc[f'{camera}LASTFILE'].read()
        print(lastfile)
        return lastfile

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        parser.add_argument('camera', type=str,
                            choices=['SCI', 'CAHK', 'CAL', 'EXT'],
                            help='The FVC camera')
        return super().add_cmdline_args(parser, cfg)
