from pathlib import Path

import ktl

from kpf import log, cfg, check_input
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


class FVCLastfile(KPFFunction):
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
    def pre_condition(cls, args):
        check_input(args, 'camera', allowed_values=['SCI', 'CAHK', 'CAL', 'EXT'])

    @classmethod
    def perform(cls, args):
        camera = args.get('camera')
        kpffvc = ktl.cache('kpffvc')
        lastfile = kpffvc[f'{camera}LASTFILE'].read()
        print(lastfile)
        return lastfile

    @classmethod
    def post_condition(cls, args):
        pass

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('camera', type=str,
                            choices=['SCI', 'CAHK', 'CAL', 'EXT'],
                            help='The FVC camera')
        return super().add_cmdline_args(parser)
