from pathlib import Path

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class FVCLastfile(KPFTranslatorFunction):
    '''Print the value of the kpffvc.[camera]LASTFILE keyword to STDOUT
    
    ARGS:
    =====
    :camera: Which FVC camera (SCI, CAHK, EXT, CAL)?
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
        '''The arguments to add to the command line interface.
        '''
        parser.add_argument('camera', type=str,
                            choices=['SCI', 'CAHK', 'CAL', 'EXT'],
                            help='The FVC camera')
        return super().add_cmdline_args(parser, cfg)
